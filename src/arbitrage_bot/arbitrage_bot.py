from typing import Optional, Type, Dict, List, Any, Union
from src.exchange_api.exchange_factory import ExchangeFactory
from src.arbitrage_bot.order import Order
from src.exchange_api.binance_proxy import BinanceProxy
from src.exchange_api.buda_proxy import BudaProxy
from src.arbitrage_bot.constants import MIN_AMOUNT_REQUIREMENTS
import logging
import time

logger = logging.getLogger(__name__)


class ArbitrageBot:
    def __init__(self, exchange_high_liquidity: str, exchange_low_liquidity: str, price_diff_threshold: float,
                 base_currency: str, quote_currency: str, amount: float, mode: Optional[str] = 'conservative'):
        """
        Initializes the arbitrage bot with the specified exchanges, price difference threshold,
        and mode for order execution.

        :param exchange_high_liquidity: The exchange where an order can be executed fast (e.g., 'binance').
        :param exchange_low_liquidity: The exchange where an order can not be executed fast (e.g., 'buda').
        :param price_diff_threshold: The minimum price difference (in percentage) to trigger arbitrage.
        :param mode: The mode of operation for the bot (e.g., 'aggressive', 'conservative').
        :param base_currency: The base currency of the trading pair (e.g., 'btc').
        :param quote_currency: The quote currency of the trading pair (e.g., 'usd').
        :param amount: The total amount to be traded for arbitrage.
        """
        self.exchange_high_liquidity = self._create_exchange(exchange_high_liquidity)
        self.exchange_low_liquidity = self._create_exchange(exchange_low_liquidity)
        self.price_diff_threshold = price_diff_threshold
        self.mode = mode
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.amount = amount

    @staticmethod
    def _create_exchange(exchange_name: str) -> Type[BinanceProxy or BudaProxy]:
        """
        Factory method to create exchange instances based on the exchange name.

        :param exchange_name: The name of the exchange (e.g., 'binance', 'buda').
        :return: The exchange class instance.
        :raises ValueError: If an unsupported exchange is provided.
        """
        return ExchangeFactory.get_exchange(exchange_name)

    def get_min_amount_for_market(self) -> float:
        """
        Retrieve the minimum amount for the current market (base_currency-quote_currency).

        :return: The minimum amount required by this market.
        """
        market_name = f"{self.base_currency.upper()}-{self.quote_currency.upper()}"
        min_amt = MIN_AMOUNT_REQUIREMENTS.get(market_name)
        if min_amt is None:
            # If not found, decide how to handle: raise an error or default to 0
            raise ValueError(f"No minimum amount configured for market {market_name}")
        return min_amt

    def get_price_difference(self) -> float:
        """
        Calculates the price difference between the two exchanges in percentage.

        :return: The price difference in percentage.
        """

        # ToDo: Adapt to real API calls
        price_a = self.exchange_high_liquidity.get_price(self.base_currency, self.quote_currency)
        price_b = self.exchange_low_liquidity.get_price(self.base_currency, self.quote_currency)

        price_diff = abs(price_a - price_b) / min(price_a, price_b) * 100
        return price_diff

    def place_sub_orders(self, sub_orders: List[Dict[str, Any]]) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Place a batch of sub-orders on the low-liquidity exchange and handle partial or complete success,
        as well as common errors. Also wait for sub-orders that are in 'received' state to transition
        to another state (e.g. 'pending', 'canceled', etc.) before returning.

        :param sub_orders: A list of sub-orders in standardized format, e.g.:
                           [
                               {
                                 "mode": "place",
                                 "order": {
                                     "amount": 0.0012,
                                     "limit": 15000000,
                                     "market_name": "eth-cop",
                                     "price_type": "limit",
                                     "type": "Bid"
                                 }
                               },
                               ...
                           ]
        :return:
            - On success (partial or complete), a list of sub-order responses in standardized format, e.g.:
              [
                {
                  "id": "1306565374",
                  "status": "received",
                  "error_message": None or "null",
                  "amount": ["0.001000001", "ETH"]
                },
                ...
              ]
            - On failure, a dictionary with "error_code" and "message" (and possibly "details"), e.g.:
              {
                "error_code": "EXCHANGE_HTTP_ERROR",
                "message": "Connection timed out"
              }
        """
        logger.info("Placing sub-orders on low-liquidity exchange: %s", sub_orders)
        try:
            # Place the sub-orders on the exchange
            standardized_response = self.exchange_low_liquidity.batch_creation(sub_orders)

            # Assume it's a list of sub-order responses (partial or complete success)
            logger.info("Exchange sub-order placement response: %s", standardized_response)

            # Validate if any sub-order is "unprepared" (insufficient funds)
            # or references an "amount_less_than_minimum" error
            error_result = self._handle_unprepared_or_minimum_amount_errors(standardized_response)
            if error_result is not None:
                # ToDo: Aca hay que mirar si se pueden resolver los errores en la anterior funcion
                # if we decide to stop the entire process upon seeing these errors
                return error_result

            # Identify sub-orders that are in 'received' state => we poll for final status.
            # I.e., we wait until the orders are indeed processed by the exchange_low_liquidity sever
            received_orders = [o for o in standardized_response if o.get("status") == "received"]
            if received_orders:
                self._wait_for_orders_to_leave_received(received_orders)

            return standardized_response

        except Exception as e:
            # Catch unexpected issues such as network errors
            logger.error("Failed to place sub-orders on exchange: %s", e, exc_info=True)
            return {
                "error_code": "EXCHANGE_HTTP_ERROR",
                "message": str(e)
            }

    @staticmethod
    def _handle_unprepared_or_minimum_amount_errors(sub_order_responses: Union[List[Dict[str, Any]], Dict[str, Any]]) \
            -> Union[None, Dict[str, Any]]:
        """
        Check for:
          1) Sub-orders in 'unprepared' state or referencing 'insolvent' errors (partial success scenario).
          2) A top-level error_code like 'EXCHANGE_API_ERROR_invalid_record' with
             'amount_less_than_minimum' in 'details' (global minimum-amount violation).

        :param sub_order_responses: Could be:
            - A list of sub-order dicts (partial success).
            - A dict with 'error_code' if it's a global error from Buda (e.g. 'amount_less_than_minimum').
        :return: None if no critical errors found, or a dict with 'error_code' and 'message' (and possibly 'sub_order').
        """

        if isinstance(sub_order_responses, dict) and "error_code" in sub_order_responses:
            error_code = sub_order_responses["error_code"]
            # For clarity, if 'EXCHANGE_API_ERROR_invalid_record' is combined with 'code': 'amount_less_than_minimum'
            # in details, it is translated to a known local error code.
            details = sub_order_responses.get("details", [])
            if (error_code == "EXCHANGE_API_ERROR_invalid_record" and
                    any(d.get("code") == "amount_less_than_minimum" for d in details)):
                logger.error("Global 'amount_less_than_minimum' error: %s", sub_order_responses)
                return {
                    "error_code": "AMOUNT_LESS_THAN_MINIMUM",
                    "message": "One or more orders had an amount less than the exchange minimum.",
                    "details": details
                }
            else:
                # It's some other global error;
                # Return it as is, or adapt the structure for consistency
                logger.error("Received a global error code from Buda: %s", sub_order_responses)
                return sub_order_responses

        # Assumption 2: it's a list of sub-order responses => partial success scenario
        if isinstance(sub_order_responses, list):
            for order_resp in sub_order_responses:
                status = order_resp.get("status")
                error_msg = order_resp.get("error_message")

                # (a) 'unprepared' => insufficient funds / "insolvent"
                if status == "unprepared":
                    logger.error("Found 'unprepared' sub-order: %s", order_resp)
                    return {
                        "error_code": "INSUFFICIENT_FUNDS",
                        "message": "One or more sub-orders could not be processed (insolvent).",
                        "sub_order": order_resp
                    }

                # (b) Check if sub-order explicitly references 'amount_less_than_minimum' in error_msg
                if error_msg and "amount_less_than_minimum" in error_msg:
                    logger.error("Found 'amount_less_than_minimum' error in sub-order: %s", order_resp)
                    return {
                        "error_code": "AMOUNT_LESS_THAN_MINIMUM",
                        "message": "A sub-order had an amount less than the minimum required.",
                        "sub_order": order_resp
                    }

            # If we got through the entire list with no errors, return None
            return None

        # 3. If none of the above conditions matched (edge case: unknown data shape):
        logger.warning("Unknown structure for sub_order_responses: %s", sub_order_responses)
        return None

    def _wait_for_orders_to_leave_received(self, received_orders: List[Dict[str, Any]], max_wait_seconds: int = 10) \
            -> None:
        """
        Wait for sub-orders in 'received' state to transition to another state ('pending', 'canceled', etc.).
        Polls the exchange's get_order_states endpoint until the orders are no longer 'received' or until
        max_wait_seconds is reached.

        :param received_orders: The sub-order responses that are in 'received' state.
        :param max_wait_seconds: How long to keep polling before giving up.
        :return: None (updates the list in-place).
        """
        logger.info("Waiting for %d sub-orders to transition out of 'received'...", len(received_orders))
        start_time = time.time()

        # We'll store the IDs of the sub-orders that are 'received'
        received_ids = [o["id"] for o in received_orders if o["id"] is not None]
        if not received_ids:
            return

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                logger.warning(
                    "Some sub-orders remained 'received' after %d seconds: %s",
                    max_wait_seconds, received_ids
                )
                break

            # Sleep briefly to avoid spamming
            time.sleep(0.2)

            # 1. Retrieve updated states from the exchange
            states_response = self.exchange_low_liquidity.get_order_states(
                self.base_currency, self.quote_currency
            )
            all_states = states_response.get("orders", [])

            # 2. Update the sub-orders that are 'received'
            for st in all_states:
                st_id = st.get("id")
                st_state = st.get("state")
                if st_id in received_ids and st_state != "received":
                    # Update the order's state in received_orders
                    for ro in received_orders:
                        if ro["id"] == st_id:
                            ro["status"] = st_state
                    # Remove from the 'received_ids' list
                    received_ids.remove(st_id)

            if not received_ids:  # all updated
                logger.info("All 'received' sub-orders transitioned to another state.")
                break

    def check_sub_orders_status(self, sub_order_ids: List[str]) -> Dict[dict, Any]:
        """
        Check the status of a batch of sub-orders.

        :param sub_order_ids: A list of sub-order IDs to check.
        :return: A dict containing dicts with the sub_orders information.
        """

        orders_information = self.exchange_low_liquidity.get_order_states(self.base_currency, self.quote_currency)
        sub_orders_info = {}
        for order in orders_information.get("orders", []):
            order_id_str = str(order.get("id"))
            if order_id_str and order_id_str in sub_order_ids:
                sub_orders_info[str(order.get("id"))] = order

        return sub_orders_info

    @staticmethod
    def execute_opposite_order_on_target_exchange(amount: float, side: str, price: float) -> Dict[str, Any]:
        """
        Execute the opposite order on the target exchange. This is a placeholder.

        :param amount: The amount to trade.
        :param side: 'buy' or 'sell'.
        :param price: Price at which to place the order.
        :return: A dict with execution details.
        """
        # ToDo: Create logic to execute market orders in the desired exchange
        logger.info(f"Executing opposite order on target exchange: {side} {amount} at {price}")
        return {"status": "executed", "executed_amount": amount, "price": price}

    def split_order_into_suborders(self, order_amount: float, reference_price: float, side: str,
                                   delta: Optional[float] = None) -> Any:
        """
        Split the given amount into multiple sub-orders taking as a reference `reference_price`.

        :param order_amount: The total amount to split.
        :param reference_price: The price to use as a base for calculation.
        :param side: 'bid' or 'ask' - the side of the market.
        :param delta: Optional delta to adjust the price.
        :return: A list of dicts with the structure:
                 [
                    {"mode": "place", "order": {...}},
                    {"mode": "place", "order": {...}},
                    {"mode": "place", "order": {...}}
                 ]
        """

        logger.info("Splitting order into sub-orders: amount=%s, reference_price=%s, side=%s, delta=%s",
                    order_amount, reference_price, side, delta)

        side = side.lower()
        sub_orders_info = [{}, {}, {}]
        # Calculate base price depending on side and delta

        if side == 'ask':
            if delta is not None:
                sub_order_one_price = reference_price + delta
            else:
                sub_order_one_price = reference_price + self.price_diff_threshold
            sub_order_two_price = sub_order_one_price * 1.001
            sub_order_three_price = sub_order_one_price * 1.002
        elif side == 'bid':
            if delta is not None:
                sub_order_one_price = reference_price - delta
            else:
                sub_order_one_price = reference_price - self.price_diff_threshold
            sub_order_two_price = sub_order_one_price * 0.999
            sub_order_three_price = sub_order_one_price * 0.998
        else:
            raise ValueError("Side must be either 'bid' or 'ask'.")

        # Amount distribution
        sub_order_one_amount = order_amount * 0.6
        sub_order_two_amount = order_amount * 0.3
        sub_order_three_amount = order_amount * 0.1

        sub_orders_info[0]["price"] = sub_order_one_price
        sub_orders_info[1]["price"] = sub_order_two_price
        sub_orders_info[2]["price"] = sub_order_three_price
        sub_orders_info[0]["amount"] = sub_order_one_amount
        sub_orders_info[1]["amount"] = sub_order_two_amount
        sub_orders_info[2]["amount"] = sub_order_three_amount

        # Construct the orders structure
        # Assuming a market_name pattern like "BASE-QUOTE", here we use the class attributes
        market_name = f"{self.base_currency}-{self.quote_currency}"

        def place_sub_order(sub_order_amount: float, sub_order_price: float, market: str, market_side: str) -> Dict:
            """
            Fills the sub_order template with a new sub_order's information.

            :param sub_order_amount: amount to trade
            :param sub_order_price: limit price
            :param market: market name
            :param market_side: side of the intended operation ('Bid' or 'Ask')
            :return: the filled sub_order
            """
            sub_order_template = {
                "mode": "place",
                "order": {
                    "amount": sub_order_amount,
                    "limit": sub_order_price,
                    "market_name": market,
                    "price_type": "limit",
                    "type": market_side
                }
            }

            return sub_order_template

        sub_orders = []

        for sub_order in sub_orders_info:
            sub_orders.append(place_sub_order(sub_order.get("amount"), sub_order.get("price"), market_name, side))

        # Enforce minimum amounts
        result = self._enforce_minimum_amounts(sub_orders, side)

        # If result is a dict with 'code', we treat it as an error
        if isinstance(result, dict) and "code" in result:
            logger.error("Enforcing min amounts failed: %s", result)
            return result

        logger.info("Created sub-orders after enforcing min amounts: %s", result)
        return result

    def _enforce_minimum_amounts(self, sub_orders: List[Dict[str, Any]], side: str) -> Any:
        """
        Enforces the minimum amount requirement for sub-orders.

        1) If the total is below the market's minimum, return an error dict with a short code.
        2) Otherwise, for each sub-order that is below the minimum:
            - Merge it into the single "target" sub-order.
              - For 'ask', merge into the sub-order with the lowest price.
              - For 'bid', merge into the sub-order with the highest price.
        3) If after merging, we still have no valid sub-orders, return an error dict.

        :param sub_orders: List of sub-order dicts.
        :param side: 'bid' or 'ask'.
        :return: A list of valid sub-orders or an error dict.
        """
        min_required = self.get_min_amount_for_market()

        total_amount = sum(so["order"]["amount"] for so in sub_orders)
        if total_amount < min_required:
            logger.warning(
                "Total order amount %.8f is below the minimum %.8f for market %s",
                total_amount, min_required, f"{self.base_currency}-{self.quote_currency}"
            )
            return {
                "code": "ERROR_BELOW_MIN_TOTAL",
                "msg": "Overall order amount is below the minimum."
            }

        # Identify the "target" sub-order for merging:
        #    - For 'ask': sub-order with the lowest price
        #    - For 'bid': sub-order with the highest price
        if side == 'ask':
            # Sort ascending by price
            sub_orders_sorted = sorted(sub_orders, key=lambda x: x["order"]["limit"])
            target_sub_order = sub_orders_sorted[0]
            others = sub_orders_sorted[1:]
        else:  # side == 'bid'
            # Sort descending by price
            sub_orders_sorted = sorted(sub_orders, key=lambda x: x["order"]["limit"], reverse=True)
            target_sub_order = sub_orders_sorted[0]
            others = sub_orders_sorted[1:]

        valid_sub_orders = []
        for so in others:
            so_amount = so["order"]["amount"]
            if so_amount < min_required:
                # Merge into the target sub-order
                target_sub_order["order"]["amount"] += so_amount
                logger.debug(
                    "Merged sub-order with amount=%.8f into target sub-order. New target amount=%.8f",
                    so_amount, target_sub_order["order"]["amount"]
                )
            else:
                valid_sub_orders.append(so)

        # Always keep the target sub-order
        valid_sub_orders.append(target_sub_order)

        if side == 'ask':
            valid_sub_orders = sorted(valid_sub_orders, key=lambda x: x["order"]["limit"])
        else:
            valid_sub_orders = sorted(valid_sub_orders, key=lambda x: x["order"]["limit"], reverse=True)

        return valid_sub_orders

    def execute_arbitrage(self) -> Dict:
        """
        Executes the arbitrage strategy if the price difference between the two exchanges exceeds
        the defined threshold. The bot will place orders on both exchanges accordingly.

        :return: A dictionary with the result of the arbitrage execution.
        """
        price_diff = self.get_price_difference()
        if price_diff < self.price_difference:
            return {"status": "no arbitrage", "price_diff": price_diff}

        # Decide whether to place limit or market orders based on the mode
        if self.mode == 'aggressive':
            order_type = 'market'
        elif self.mode == 'conservative':
            order_type = 'limit'
        else:
            raise ValueError("Unsupported mode. Use 'aggressive' or 'conservative'.")

        # Create and place orders
        order_a = Order(self.base_currency, self.quote_currency, self.amount / 2, order_type=order_type)
        order_b = Order(self.base_currency, self.quote_currency, self.amount / 2, order_type=order_type)

        # Place orders on both exchanges
        order_a_response = self.exchange_high_liquidity.new_order(order_a)
        order_b_response = self.exchange_low_liquidity.new_order(order_b)

        return {
            "status": "arbitrage executed",
            "order_a": order_a_response,
            "order_b": order_b_response,
            "price_diff": price_diff
        }

    def conservative_strategy(self, target_exchange_price: float, price_diff_threshold: float,
                              order: Order, delta: float) -> Dict[str, Any]:
        """
        Executes the conservative strategy logic.

        :param target_exchange_price: The current price of the target exchange (e.g. Binance price).
        :param price_diff_threshold: The minimum price difference threshold to trigger the strategy.
        :param order: The Order instance to work with.
        :param delta: A minimum gap used to adjust the target price of the sub-orders.
        :return: A dictionary with information about the operation performed.
        """
        logger.info("Starting conservative strategy...")

        # Determine if this is a new order or previously created
        # Assume: If order.sub_orders is empty => new order, else => previously created
        previously_created = len(order.sub_orders) > 0

        low_liquidity_exchange = "buda"  # Example: low liquidity exchange
        high_liquidity_exchange = "binance"  # Example: high liquidity exchange

        if not previously_created:
            # New Order scenario
            # Get order_book from low liquidity exchange
            order_book = self.get_order_book(low_liquidity_exchange, order.base_currency, order.quote_currency)
            bids = order_book.get("bids", [])
            asks = order_book.get("asks", [])

            # Extract placeholders for prices:
            # In reality, you'd determine which prices correspond to p_binance, buda_lowest_ask, etc.
            p_binance = target_exchange_price
            buda_lowest_ask = asks[0][0] if asks else p_binance * 1.01  # Placeholder
            buda_highest_bid = bids[0][0] if bids else p_binance * 0.99  # Placeholder
            highest_bid = buda_highest_bid  # Could be something else if we differentiate.

            # Check order type
            if order.order_type == 'bid_limit':
                # p_diff = (p_binance - buda_lowest_ask) / buda_lowest_ask
                p_diff = (p_binance - buda_lowest_ask) / buda_lowest_ask

                if p_diff > price_diff_threshold:
                    # Split into batch of buda_limit_bid sub_orders at price = buda_lowest_ask - delta
                    sub_orders = self.split_order_into_suborders(order, buda_lowest_ask - delta, side='buy')
                else:
                    # p_diff <= price_diff_treshold
                    # Split into batch of buda_limit_bid sub_orders at price = binance_price - price_diff_treshold
                    sub_orders = self.split_order_into_suborders(order, p_binance - price_diff_threshold, side='buy')

                # Place sub orders
                responses = self.place_sub_orders(low_liquidity_exchange, sub_orders)
                order.sub_orders = responses
                return {
                    "status": "sub_orders_placed",
                    "sub_orders": responses
                }

            else:
                # order_type != 'bid_limit' => treat as ask scenario
                # p_diff = (highest_bid - p_binance) / p_binance
                p_diff = (buda_highest_bid - p_binance) / p_binance

                if p_diff > price_diff_threshold:
                    # Split into buda_limit_ask at price = buda_highest_bid + delta
                    sub_orders = self.split_order_into_suborders(order, buda_highest_bid + delta, side='sell')
                else:
                    # Split into buda_limit_ask at price = binance_price + price_diff_treshold
                    sub_orders = self.split_order_into_suborders(order, p_binance + price_diff_threshold, side='sell')

                responses = self.place_sub_orders(low_liquidity_exchange, sub_orders)
                order.sub_orders = responses
                return {
                    "status": "sub_orders_placed",
                    "sub_orders": responses
                }

        else:
            # Previously created order, check status
            sub_order_ids = [o["id"] for o in order.sub_orders]
            statuses = self.check_sub_orders_status(low_liquidity_exchange, sub_order_ids)

            # Check if any sub_order traded or partially_traded
            traded_statuses = ['traded', 'parcially_traded']
            any_traded = any(s["status"] in traded_statuses for s in statuses)

            if any_traded:
                # Execute opposite order on target exchange
                executed_amount = sum(s["amount"] for s in order.sub_orders if s["status"] in traded_statuses)
                side = 'sell' if order.order_type == 'bid_limit' else 'buy'
                opposite_order_price = target_exchange_price  # This could be refined

                opposite_response = self.execute_opposite_order_on_target_exchange(executed_amount, side, opposite_order_price)
                order.executed_amount += opposite_response["executed_amount"]

                # Cancel resting sub_orders
                # (In production, you'd call an API method to cancel each)
                for s in order.sub_orders:
                    if s["status"] not in traded_statuses:
                        s["status"] = "canceled"

                return {
                    "status": "opposite_order_executed",
                    "executed_amount": order.executed_amount,
                    "opposite_order_response": opposite_response
                }
            else:
                # No sub_order traded, cancel them
                for s in order.sub_orders:
                    s["status"] = "canceled"
                return {
                    "status": "sub_orders_canceled"
                }

