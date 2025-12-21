from typing import Optional, Type, Dict, List, Any, Union
from concurrent.futures import ThreadPoolExecutor
from src.exchange_api.exchange_factory import ExchangeFactory
from src.arbitrage_bot.order import Order
from src.exchange_api.binance_proxy import BinanceProxy
from src.exchange_api.buda_proxy import BudaProxy
from src.arbitrage_bot.constants import MIN_AMOUNT_REQUIREMENTS, MIN_AMOUNT_BINANCE_REQUIREMENTS, MIN_BTC_PER_INVOICE, \
    MAX_BTC_PER_INVOICE, MIN_WITHDRAWAL_AMOUNT_BINANCE
from src.order_types.arbitrage_order import ArbitrageOrder
from src.order_types.encoders import OrderType, CurrencyOfInterest
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
        self.currency_of_interest = CurrencyOfInterest.QUOTE  # Defines the currency to accumulate base or quote (e.g. BTCUSDC, base=BTC)

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

    def get_price_difference(self, high_liquidity_price: float, arb_order: "ArbitrageOrder") -> float:
        """
        Retrieve the order book from the low-liquidity exchange and compute a price difference (%)
        relative to `high_liquidity_price`.

        Workflow:
          1) Call `get_order_book(...)` on the low-liquidity exchange; parse the resulting asks/bids.
          2) If `arb_order.order_type` in [BUY_LIMIT, BUY_MARKET], use:
               p_diff = (highest_bid - high_liquidity_price) / high_liquidity_price
             If `arb_order.order_type` in [SELL_LIMIT, SELL_MARKET], use:
               p_diff = (high_liquidity_price - lowest_ask) / lowest_ask
          3) Return p_diff as a decimal fraction. For example, 0.05 means 5%.

        :param high_liquidity_price: The asset price on the high-liquidity exchange (float).
        :param arb_order: The `ArbitrageOrder` describing the operation type (BUY or SELL).
        :return: A float representing the price difference in decimal form (e.g. 0.05 = 5%).
        :raises RuntimeError: If the order book is missing or invalid, or if top-level fields are missing.
        """
        logger.info(
            "Computing price difference with high_liquidity_price=%.6f for order_type=%s",
            high_liquidity_price, arb_order.order_type.name
        )

        # 1) Fetch the order book from the low-liquidity exchange
        response_data: Dict[str, Any] = self.exchange_low_liquidity.get_order_book()
        if "order_book" not in response_data or not response_data["order_book"]:
            raise RuntimeError("Missing 'order_book' in low-liquidity response.")
        order_book = response_data["order_book"]

        asks = order_book.get("asks", [])
        bids = order_book.get("bids", [])

        if not asks or not bids:
            raise RuntimeError("Order book is missing asks/bids data.")

        # 2) Convert all asks/bids to floats, ensuring positivity
        #    Then find the minimum ask, maximum bid
        try:
            float_asks = [float(ask[0]) for ask in asks]
            float_bids = [float(bid[0]) for bid in bids]
        except (ValueError, IndexError) as e:
            logger.error("Failed to parse order book prices: %s", e)
            raise RuntimeError("Invalid order book data: cannot parse asks/bids as floats.")

        # Confirm all are > 0
        if any(price <= 0 for price in float_asks + float_bids):
            raise RuntimeError("Found non-positive price in the order book, which is invalid.")

        # The true lowest ask is min(...)
        lowest_ask = min(float_asks)
        # The true highest bid is max(...)
        highest_bid = max(float_bids)

        # 3) Decide formula based on order_type
        order_type_name = arb_order.order_type
        if order_type_name in [OrderType.BUY_LIMIT, OrderType.BUY_MARKET]:
            # p_diff = (high_liquidity_price - lowest_exchange_lowest_ask) / lowest_exchange_lowest_ask
            p_diff = (high_liquidity_price - lowest_ask) / lowest_ask
        elif order_type_name in [OrderType.SELL_LIMIT, OrderType.SELL_MARKET]:
            # p_diff = (lowest_exchange_highest_bid - high_liquidity_price) / high_liquidity_price
            p_diff = (highest_bid - high_liquidity_price) / high_liquidity_price
        else:
            logger.error("Unrecognized order type for price diff: %s", order_type_name)
            return 0.0  # or raise an exception

        logger.info(
            "Computed price diff=%.4f for order_type=%s (lowest_ask=%.4f, highest_bid=%.4f, high_price=%.4f)",
            p_diff, order_type_name, lowest_ask, highest_bid, high_liquidity_price
        )
        return p_diff

    def place_sub_orders(self, sub_orders: List[Dict[str, Any]], arb_order: ArbitrageOrder) -> \
            Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Place a batch of sub-orders on the low-liquidity exchange and handle partial or complete success,
        as well as common errors. Also wait for sub-orders that are in 'received' state to transition
        to another state (e.g. 'pending', 'canceled', etc.) before returning.

        :param sub_orders: A list of sub-orders in standardized format.
        :param arb_order: The ArbitrageOrder object to update with traded amounts or partial fills.
        :return:
            - On success (partial or complete), a list of sub-order responses in standardized format
            - On failure, a dictionary with "error_code" and "message" (and possibly "details").
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
                # TODO: ES CRUCIAL RESOLVER ESTO
                # ToDo: Here it is necessary to see if the errors in the previous function can be solved.
                return error_result

            # Identify sub-orders that are in 'received' state => we poll for final status.
            # I.e., we wait until the orders are indeed processed by the exchange_low_liquidity sever
            received_orders = [o for o in standardized_response if o.get("status") == "received"]
            if received_orders:
                self._wait_for_orders_to_leave_received(received_orders, arb_order)

            return standardized_response

        except Exception as e:
            # Catch unexpected issues such as network errors
            logger.error("Failed to place sub-orders on exchange: %s", e, exc_info=True)
            return {
                "error_code": "EXCHANGE_HTTP_ERROR",
                "message": str(e)
            }

    def place_sub_order_cancellations(self, sub_orders: List[Dict[str, Any]], arb_order: ArbitrageOrder) -> \
            List[Dict[str, Any]]:
        """
        Cancel a batch of sub-orders on the low-liquidity exchange. If any sub-order transitions to
        'canceled_and_traded' (or partial traded states), the ArbitrageOrder object is updated accordingly.

        :param sub_orders: A list of sub-order dicts from a SUCCESSFUL place_sub_orders call,
                           each presumably with an 'id' to identify the order on the exchange.
        :param arb_order: The ArbitrageOrder object to be updated if partial trades occur during cancellation.
        :return: A list of sub-order dicts summarizing the cancellation operations (mode='cancel', order_id=...).
        """
        logger.info("Cancelling sub-orders on low-liquidity exchange: %s", sub_orders)

        # 1. Build 'cancel' instructions
        cancel_requests = []
        for so in sub_orders:
            # Suppose each sub-order has an 'id'
            order_id = so.get("id")
            if order_id:
                cancel_requests.append({"mode": "cancel", "order_id": order_id})

        if not cancel_requests:
            logger.info("No sub-orders to cancel.")
            return []

        # 2. Call batch_cancellation
        cancel_response = self.exchange_low_liquidity.batch_cancellation(cancel_requests)
        cancelled_orders_id = [order_id.get('order_id') for order_id in cancel_response['orders_diff']]
        logger.info("Exchange sub-order cancellation response: %s", cancel_response)

        states_response = self.exchange_low_liquidity.get_order_states(self.base_currency, self.quote_currency)
        all_states = states_response.get("orders", [])

        # 3. If any sub-order is 'canceled_and_traded' or partial, update the ArbitrageOrder object
        #    using `_update_arbitrage_order_on_fill`
        standardized_cancel_responses = []
        for st in all_states:
            st_id = st.get("id")
            if st_id in cancelled_orders_id:
                st_state = st.get("state")
                base_currency_traded_amount = float(st.get("traded_amount", 0.0)[0])
                quote_currency_traded_amount = float(st.get("total_exchanged", 0.0)[0])

                self._update_arbitrage_order_on_fill(
                    sub_order_dict=so,
                    new_state=st_state,
                    traded_base_amount=base_currency_traded_amount,
                    traded_quote_amount=quote_currency_traded_amount,
                    arb_order=arb_order
                )

                sub_order_cancelled = {
                    "id": st_id,
                    "status": st_state,
                    "error_message": "null",
                    "amount": st.get("amount"),
                    "traded_amount": st.get("traded_amount"),
                    "total_exchanged": st.get("total_exchanged")
                }
                standardized_cancel_responses.append(sub_order_cancelled)

        return standardized_cancel_responses

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

    def _wait_for_orders_to_leave_received(self, received_orders: List[Dict[str, Any]],
                                           arb_order: ArbitrageOrder, max_wait_seconds: int = 10) -> None:
        """
        Wait for sub-orders in 'received' state to transition to another state.
        If the sub-order transitions to a traded-related state, update `arb_order` dynamic amounts.

        :param received_orders: The sub-order responses that are in 'received' state.
        :param arb_order: The ArbitrageOrder to update with partial/traded amounts.
        :param max_wait_seconds: How long to keep polling before giving up.
        :return: None (updates the sub-orders in-place, updates `arb_order` amounts).
        """
        logger.info("Waiting for %d sub-orders to transition out of 'received'...", len(received_orders))
        start_time = time.time()

        # We store the IDs of sub-orders that are 'received'
        received_ids = [o["id"] for o in received_orders if o.get("id") is not None]
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

            # Sleep briefly
            time.sleep(0.2)

            # 1. Retrieve updated states from the exchange
            states_response = self.exchange_low_liquidity.get_order_states(self.base_currency, self.quote_currency)
            all_states = states_response.get("orders", [])

            # 2. Update sub-orders that are 'received'
            for st in all_states:
                st_id = st.get("id")
                st_state = st.get("state")

                if st_id in received_ids and st_state != "received":
                    # The sub-order has transitioned out of 'received'
                    # Find the matching sub-order
                    for ro in received_orders:
                        if ro["id"] == st_id:
                            ro["status"] = st_state
                            # Potentially the exchange server might return a 'traded_amount' field or similar
                            # to indicate how much was actually traded in this sub-order fill.
                            # We'll fetch that and update `arb_order`.
                            base_currency_traded_amount = float(st.get("traded_amount", 0.0)[0])
                            quote_currency_traded_amount = float(st.get("total_exchanged", 0.0)[0])

                            self._update_arbitrage_order_on_fill(
                                sub_order_dict=ro,
                                new_state=st_state,
                                traded_base_amount=base_currency_traded_amount,
                                traded_quote_amount=quote_currency_traded_amount,
                                arb_order=arb_order
                            )

                    # Remove from 'received_ids'
                    received_ids.remove(st_id)

            if not received_ids:
                logger.info("All 'received' sub-orders transitioned to another state.")
                break

    def _update_arbitrage_order_on_fill(self, sub_order_dict: Dict[str, Any], new_state: str,
                                        traded_base_amount: float, traded_quote_amount: float,
                                        arb_order: 'ArbitrageOrder') -> None:
        """
        Update the ArbitrageOrder's dynamic attributes (e.g. traded_amount_low_liquidity,
        pending_amount_low_liquidity) whenever a sub-order transitions to a 'traded' state.

        :param sub_order_dict: The sub-order that changed states.
        :param new_state: The new state (e.g., 'traded', 'canceled_and_traded', 'partially_traded').
        :param traded_base_amount: The float indicating how much was actually traded on the low-liquidity side
        of the base currency.
        :param traded_quote_amount: The float indicating how much was actually traded on the low-liquidity side
        of the qupte currency.
        :param arb_order: The ArbitrageOrder object to update.
        """

        traded_amount = traded_quote_amount  # The traded amount is expressed in quote_currency, bcs usually it is FIAT
        if new_state in ("traded", "canceled_and_traded", "pending") and traded_amount > 0:
            logger.info(
                "Sub-order %s changed state to %s with traded_amount=%.4f. Updating ArbitrageOrder.",
                sub_order_dict.get("id"), new_state, traded_amount
            )
            # Increase the traded_amount_low_liquidity
            # Recompute pending_amount_low_liquidity = original_amount - traded_amount_low_liquidity
            # Update the pending amount to trade in the high liquidity exchange
            arb_order.update_low_liquidity_traded(traded_quote_delta=traded_quote_amount,
                                                  traded_base_delta=traded_base_amount)
            # If partial, we keep trying. If fully filled, we might see if pending_amount is close to zero.
            self.execute_opposite_order_high_liquidity_exchange(arb_order)

        else:
            logger.info(
                "Sub-order %s changed state to %s with no fill update. (traded_amount=%.4f)",
                sub_order_dict.get("id"), new_state, traded_amount
            )
        # Possibly add more logic if new_state = 'canceled' or 'pending', etc.

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

    def execute_opposite_order_high_liquidity_exchange(self, arb_order: 'ArbitrageOrder') \
            -> Union[Dict[str, Any], Dict[str, Any]]:
        """
        Synchronously place a MARKET order on the high-liquidity exchange for the
        arb_order.pending_amount_high_liquidity, then call arb_order.fulfill_high_liquidity(...)
        with the executed quantity.
        """
        symbol = arb_order.base_currency.upper() + arb_order.quote_currency.upper()

        to_trade_quote_currency = arb_order.get_pending_quote_amount_high_liquidity
        to_trade_base_currency = arb_order.get_pending_base_amount_high_liquidity  # Pending amount, in base currency

        if arb_order.order_type in [OrderType.BUY_LIMIT, OrderType.BUY_MARKET]:
            side = "SELL"
        elif arb_order.order_type in [OrderType.SELL_LIMIT, OrderType.SELL_MARKET]:
            side = "BUY"
        if to_trade_quote_currency <= MIN_AMOUNT_BINANCE_REQUIREMENTS.get(symbol, 0.0):
            logger.info("No pending amount to trade in the high-liquidity side.")
            return {"msg": "No pending amount to trade."}

        logger.info("Placing MARKET order on high-liquidity exchange: side=%s, qty=%.4f", side, to_trade_quote_currency)
        try:
            if self.currency_of_interest == CurrencyOfInterest.QUOTE:  # Want to accumulate quote currency
                order_resp = self.exchange_high_liquidity.new_order(
                    base_currency=self.base_currency,
                    quote_currency=self.quote_currency,
                    side=side.upper(),
                    order_type='MARKET',
                    quantity=round(to_trade_base_currency, 5),  # Amount expressed in base currency
                )
            elif self.currency_of_interest == CurrencyOfInterest.BASE:  # Want to accumulate base currency
                order_resp = self.exchange_high_liquidity.new_order(
                    base_currency=self.base_currency,
                    quote_currency=self.quote_currency,
                    side=side.upper(),  # Must be either `SELL` or `BUY`
                    order_type='MARKET',
                    quote_order_qty=to_trade_quote_currency,  # Amount expressed in quote currency
                )

            if "code" in order_resp and order_resp["code"] < 0:
                logger.error("High-liquidity exchange error: %s", order_resp)
                return order_resp

            executed_base_qty = float(order_resp.get("executedQty", 0.0))
            execution_price = float(order_resp.get("fills", [0.0])[0].get("price", 0.0))
            executed_quote_qty = round(executed_base_qty * execution_price, 5)  # Turn it back to quote currency
            arb_order.fulfill_high_liquidity(executed_quote_qty, executed_base_qty)
            arb_order.update_profit()  # TODO: se puede hacer metodo privado y encapsularlo en fulfull_high_liquidity

            return order_resp

        except Exception as e:
            logger.error("Error placing order on high-liquidity exchange: %s", e, exc_info=True)
            return {"code": -9999, "msg": str(e)}

    def split_order_into_suborders(self, order: ArbitrageOrder, reference_price: float, side: str,
                                   delta: Optional[float] = None) -> Any:
        """
        Split the given `ArbitrageOrder`'s original_amount into multiple sub-orders,
        taking `reference_price` as a base for setting limit prices.

        :param order: An `ArbitrageOrder` instance whose `original_amount` will be splitted.
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

        logger.info("Splitting order into sub-orders: order=%s, reference_price=%s, side=%s, delta=%s",
                    order, reference_price, side, delta)

        order_amount = order.pending_amount_low_liquidity

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

        # Enforce minimum amounts. This ensures that there is not an attempt to create a sub/order with less than
        # the minimum amount allowed.
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

    def funds_transfer(self, arb_order: 'ArbitrageOrder') -> bool:
        """
        Execute both btc_transfer and quote_currency_transfer in parallel, so they don't block each other.
        If both succeed, return True, else False.

        :param arb_order: The ArbitrageOrder object, containing the relevant
                          traded amounts and order type.
        :return: True if both BTC and quote currency transfers succeed, False otherwise.
        """
        logger.info("Initiating parallel funds transfer for order_type=%s", arb_order.order_type.name)

        # We'll define local functions so we can pass them to threads
        def do_btc_transfer():
            logger.debug("Starting btc_transfer...")
            return self.btc_transfer(arb_order)

        def do_quote_transfer():
            logger.debug("Starting quote_currency_transfer...")
            return self.quote_currency_transfer(arb_order)

        # Use two threads: one for BTC, one for quote currency
        with ThreadPoolExecutor(max_workers=2) as executor:
            btc_future = executor.submit(do_btc_transfer)
            quote_future = executor.submit(do_quote_transfer)

            logger.debug("Both transfers submitted; waiting for results...")

            # Wait for both tasks to complete, then gather success flags
            btc_success = btc_future.result()
            quote_success = quote_future.result()

        # Combine results
        if btc_success and quote_success:
            logger.info("All funds transferred successfully (BTC + quote).")
            logger.info("Reset order attributes.")

            arb_order.reset_values(order_completion=True)
            return True
        else:
            logger.warning("Some transfer(s) failed. btc_success=%s, quote_success=%s", btc_success, quote_success)
            return False

    # TODO: Busacar la manera de paralelizar el proceso por cada chunk
    def btc_transfer(self, arb_order: ArbitrageOrder) -> bool:
        """
        Synchronously transfer BTC between exchanges based on the arbitrage order's type.
        If order_type in [BUY_LIMIT, BUY_MARKET], we transfer from low-liquidity to high-liquidity.
        If order_type in [SELL_LIMIT, SELL_MARKET], we transfer from high-liquidity to low-liquidity.

        :param arb_order: The ArbitrageOrder containing traded_base_amount_low_liquidity.
        :return: None (raises or logs if there's an issue).
        """
        # 1. Decide sender / receiver
        if arb_order.order_type in (OrderType.BUY_LIMIT, OrderType.BUY_MARKET):
            sender = self.exchange_low_liquidity
            receiver = self.exchange_high_liquidity
        elif arb_order.order_type in (OrderType.SELL_LIMIT, OrderType.SELL_MARKET):
            sender = self.exchange_high_liquidity
            receiver = self.exchange_low_liquidity
        else:
            logger.error("Unknown order_type: %s", arb_order.order_type)
            return

        # 2. The total BTC to send
        # TODO: Esto deberia depender de arb_order.currency_of_interest ?
        total_btc = arb_order.traded_base_amount_low_liquidity
        if total_btc <= MIN_BTC_PER_INVOICE:
            logger.info("No BTC to transfer (traded_base_amount_low_liquidity=%.6f). Skipping.", total_btc)
            return

        # 3. Split into smaller chunks
        chunks = self._split_btc_amount(total_btc)
        # Track overall success
        all_success = True

        # 4) For each chunk: create invoice, pay invoice, wait for confirm
        for chunk in chunks:
            if chunk < MIN_BTC_PER_INVOICE:
                logger.warning(
                    "Chunk=%.8f is below minimum invoice=%.8f. Skipping this chunk.",
                    chunk, MIN_BTC_PER_INVOICE
                )
                continue

            # 4a) Create LN invoice on receiver
            invoice_data = receiver.create_lightning_invoice(amount=chunk)
            # TODO: Revisar si es necesario usar el uuid en vez de el id en BUDA
            ln_invoice = invoice_data.get("invoice")
            if not ln_invoice:
                logger.error(
                    "Failed to create LN invoice for chunk=%.8f on %s. invoice_data=%s",
                    chunk, receiver.__class__.__name__, invoice_data
                )
                all_success = False
                continue

            logger.info("Created LN invoice: %s for chunk=%.8f BTC", ln_invoice, chunk)

            # 4b) pay_ln_invoice from sender
            pay_response = sender.pay_ln_invoice(ln_invoice=ln_invoice, amount=chunk)
            if ("code" in pay_response and pay_response.get("code", 0) < 0) or ("error" in pay_response):
                logger.error("Invoice payment failed. pay_response=%s", pay_response)
                all_success = False
                continue

            withdraw_id = str(pay_response.get("id", ""))
            if not withdraw_id:
                logger.error("No withdraw_id found in pay_response=%s", pay_response)
                all_success = False
                continue

            logger.info("Withdrawal initiated ID=%s for chunk=%.8f BTC on %s",
                        withdraw_id, chunk, sender.__class__.__name__)

            # 4c) Wait for confirm
            success = self._wait_for_asset_withdraw(arb_order.base_currency, sender, withdraw_id)
            if not success:
                logger.error(
                    "Withdrawal ID=%s for chunk=%.8f BTC failed or timed out. Aborting this chunk.",
                    withdraw_id, chunk
                )
                all_success = False
            else:
                logger.info(
                    "Withdrawal ID=%s for chunk=%.8f BTC confirmed successfully.",
                    withdraw_id, chunk
                )

        # Final result
        if all_success:
            logger.info("All BTC chunks transferred successfully!")
        else:
            logger.error("Some BTC chunks failed to transfer or confirm.")
        return all_success

    @staticmethod
    def _split_btc_amount(total_btc: float) -> List[float]:
        """
        Split total_btc into chunks each between MIN_BTC_PER_INVOICE and MAX_BTC_PER_INVOICE.
        For example, if we have 0.017 BTC, we might produce [0.009999, 0.007001].
        """
        chunks = []
        remaining = total_btc
        while remaining > 0:
            if remaining <= MAX_BTC_PER_INVOICE:
                # If what's left is within the max, take it
                chunk = remaining
            else:
                chunk = MAX_BTC_PER_INVOICE

            chunks.append(round(chunk, 6))
            remaining -= chunk

        return chunks

    def quote_currency_transfer(self, arb_order: ArbitrageOrder) -> bool:
        """
        Synchronously transfer the quote currency between exchanges based on the arbitrage order's type.
        If order_type in [BUY_LIMIT, BUY_MARKET], we transfer from high-liquidity to low-liquidity.
        If order_type in [SELL_LIMIT, SELL_MARKET], we transfer from low-liquidity to high-liquidity.

        :param arb_order: The ArbitrageOrder containing traded_base_amount_low_liquidity.
        :return: Bool indicating success/failure of the entire operation.
        """
        # 1. Decide sender / receiver
        if arb_order.order_type in (OrderType.BUY_LIMIT, OrderType.BUY_MARKET):
            sender = self.exchange_high_liquidity
            receiver = self.exchange_low_liquidity
        elif arb_order.order_type in (OrderType.SELL_LIMIT, OrderType.SELL_MARKET):
            sender = self.exchange_low_liquidity
            receiver = self.exchange_high_liquidity
        else:
            logger.error("Unknown order_type: %s", arb_order.order_type)
            return

        # 2. The total QUOTE currency to send
        # TODO: Esto deberia depender de arb_order.currency_of_interest ?
        total_quote_currency = arb_order.traded_quote_amount_low_liquidity
        if total_quote_currency <= MIN_WITHDRAWAL_AMOUNT_BINANCE.get(arb_order.quote_currency):
            logger.info("No =%s to transfer (traded_base_amount_low_liquidity=%.6f). Skipping.",
                        arb_order.quote_currency, total_quote_currency)
            return

        # Track overall success
        all_success = True

        # TODO: Automatizar la red cuando actualicen BUDA para que soporte SOL
        deposit_address = receiver.create_quote_currency_address(coin=arb_order.quote_currency, network="ETH")
        # TODO: Revisar si es necesario usar el uuid en vez de el id en BUDA
        address = deposit_address.get("address")
        if not address:
            logger.error(
                "Failed to create a deposit address for quote=%.8f on %s. invoice_data=%s",
                total_quote_currency, receiver.__class__.__name__, deposit_address
            )
            all_success = False

        # TODO: Automatizar la red cuando actualicen BUDA para que soporte SOL
        # 4b) Send funds from sender
        withdrawal_response = sender.create_withdraw_request(
            coin=arb_order.quote_currency,
            address=address,
            amount=total_quote_currency,
            network="ETH")

        if ("code" in withdrawal_response and withdrawal_response.get("code", 0) < 0) or (
                "error" in withdrawal_response):
            logger.error("Fund transfer failed. transfer=%s", withdrawal_response)
            all_success = False

        withdraw_id = str(withdrawal_response.get("id", ""))
        if not withdraw_id:
            logger.error("No withdraw_id found in transfer=%s", withdrawal_response)
            all_success = False

        logger.info("Withdrawal initiated ID=%s for amount=%.8f BTC on %s",
                    withdraw_id, total_quote_currency, sender.__class__.__name__)

        # 4c) Wait for confirm
        success = self._wait_for_asset_withdraw(arb_order.quote_currency, sender, withdraw_id)
        if not success:
            logger.error(
                "Withdrawal ID=%s for quote=%.8f BTC failed or timed out. Aborting this transfer.",
                withdraw_id, total_quote_currency
            )
            all_success = False
        else:
            logger.info(
                "Withdrawal ID=%s for quote=%.8f confirmed successfully.",
                withdraw_id, total_quote_currency
            )

        # Final result
        if all_success:
            logger.info("All funds transferred successfully!")
        else:
            logger.error("Withdrawal failed to transfer or confirm.")
        return all_success

    # TODO: Adapt `max_wait_seconds` according to the coin, bcs, some take longer than others
    @staticmethod
    def _wait_for_asset_withdraw(
            coin: str,
            sender: Any,
            withdraw_id: str,
            max_wait_seconds: int = 60 * 6
    ) -> bool:
        """
        Wait for an asset withdrawal to be confirmed by polling the sender's
        withdraw history.

        :param coin: The Coin history of interest
        :param sender: The exchange proxy (BudaProxy or BinanceProxy) that initiated the withdrawal.
        :param withdraw_id: The unique identifier for the withdrawal request (e.g., 'WBbWyN' in Buda).
        :param max_wait_seconds: The maximum time in seconds to wait before giving up.
        :return: True if the withdrawal transitions to 'confirmed', False otherwise.
        """
        logger.info(
            "Waiting for BTC withdrawal ID=%s on sender=%s, up to %d seconds...",
            withdraw_id, sender.__class__.__name__, max_wait_seconds
        )
        start_time = time.time()
        coin = coin.upper()

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                logger.warning(
                    "Timed out waiting for BTC withdraw ID=%s to become 'confirmed'.",
                    withdraw_id
                )
                return False

            # Sleep briefly to avoid spamming the API
            time.sleep(0.5)

            # 1. Retrieve the withdraw history
            withdraw_history = sender.get_withdraw_history(coin=coin)

            # 2. Search for an entry matching 'id' == withdraw_id
            matching_withdraw = next(
                (w for w in withdraw_history if str(w.get('id')) == withdraw_id),
                None
            )

            if not matching_withdraw:
                logger.debug(
                    "Withdraw ID=%s not found in sender's withdraw_history. Retrying...",
                    withdraw_id
                )
                continue

            # 3. Check its 'state'
            state = matching_withdraw.get("state", "")
            logger.debug("Found withdraw ID=%s with state=%s", withdraw_id, state)

            # Normal flow: 'pending_confirmation' -> 'confirmed'
            # If it becomes 'confirmed', success
            if state == "confirmed":
                logger.info(
                    "Withdrawal ID=%s is now confirmed. Completed successfully.", withdraw_id
                )
                return True

            # If the state is something else (e.g. 'rejected' or 'error'),
            # we can consider that a failure or log it
            if state not in ("pending_confirmation", "confirmed", 'executing'):
                logger.error(
                    "Withdrawal ID=%s entered unexpected state=%s. Stopping.",
                    withdraw_id, state
                )
                return False

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

                opposite_response = None
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
