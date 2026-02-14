from src.exchange_api.high_liquidity_exchanges.base_high_liquidity_exchange import BaseHighLiquidityExchange
from src.exchange_api.low_liquidity_exchanges.base_low_liquidity_exchange import BaseLowLiquidityExchange
from src.exchange_api.high_liquidity_exchanges.binance_proxy import BinanceProxy
from src.arbitrage_bot.encoders import MIN_BTC_PER_INVOICE, MAX_BTC_PER_INVOICE
from src.exchange_api.low_liquidity_exchanges.buda_proxy import BudaProxy
from src.order_types.encoders import OrderType, CurrencyOfInterest
from typing import Optional, Type, Dict, List, Any, Union, Tuple
from src.exchange_api.exchange_factory import ExchangeFactory
from src.order_types.arbitrage_order import ArbitrageOrder
from src.telegram_bot.telegram_alert import TelegramAlert
from src.user_interface.arbitrage_ui import ArbitrageUI
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
import threading
import logging
import inspect
import asyncio
import json
import time

logger = logging.getLogger(__name__)


class ArbitrageBot:
    def __init__(self, exchange_high_liquidity: str, exchange_low_liquidity: str, price_diff_threshold: float,
                 base_currency: str, quote_currency: str):
        """
        Initializes the arbitrage bot with the specified exchanges, price difference threshold,
        and mode for order execution.

        :param exchange_high_liquidity: The exchange where an order can be executed fast (e.g., 'binance').
        :param exchange_low_liquidity: The exchange where an order can not be executed fast (e.g., 'buda').
        :param price_diff_threshold: The minimum price difference (in percentage) to trigger arbitrage.
        :param mode: The mode of operation for the bot (e.g., 'aggressive', 'conservative').
        :param base_currency: The base currency of the trading pair (e.g., 'btc').
        :param quote_currency: The quote currency of the trading pair (e.g., 'usd').
        """
        self.exchange_high_liquidity: BaseHighLiquidityExchange = self._create_exchange(exchange_high_liquidity)
        self.exchange_low_liquidity: BaseLowLiquidityExchange = self._create_exchange(exchange_low_liquidity)
        self.price_diff_threshold: float = price_diff_threshold / 100
        self.base_currency: str = base_currency  # To deprecate
        self.quote_currency: str = quote_currency  # To deprecate
        self.currency_of_interest: CurrencyOfInterest = CurrencyOfInterest.QUOTE  # Defines the currency to accumulate base or quote (e.g. BTCUSDC, base=BTC)
        self.low_liquidity_taker_fee: float = 0.8 / 100
        self.quote_currency_network: str = "ETH"
        self.minimum_notional_low_liquidity: float = 0.00002  # Expressed in Base Currency
        self.minimum_notional_high_liquidity: float = 5  # the minimum allowed amount to trade in a given market
        self.minimum_withdrawal_amount_quote_high_liquidity: float = 20  # USDC with ETH network
        self.websocket_mode: bool = True

        self.ui: ArbitrageUI = ArbitrageUI()
        self.telegram_alert = TelegramAlert()

    def get_min_notional_high_liquidity(self, arb_order: ArbitrageOrder) -> float:
        """
        minNotional is the minimum allowed amount to trade in a given market (expressed in quotation currency).

        Retrieves the minimum notional (minNotional) from the high-liquidity exchange's market info
        for the trading pair defined by arb_order.base_currency and arb_order.quote_currency.

        It calls the high_liquidity_exchange.get_market_info() method and searches for the symbol
        that matches the trading pair (e.g., "BTCUSDT"). Within that symbol's filters, it locates
        the filter with "filterType": "NOTIONAL" and returns the "minNotional" value as a float.

        :param arb_order: The ArbitrageOrder instance containing base_currency and quote_currency.
        :return: The minimum notional value as a float.
        :raises ValueError: If the trading pair is not found or the NOTIONAL filter is missing,
                            or if the minNotional value cannot be parsed.
        """
        market_info: Dict[str, Any] = self.exchange_high_liquidity.get_market_info(arb_order.base_currency,
                                                                                   arb_order.quote_currency)
        symbols = market_info.get("symbols", [])
        trading_pair = f"{arb_order.base_currency.upper()}{arb_order.quote_currency.upper()}"

        for symbol_data in symbols:
            if symbol_data.get("symbol") == trading_pair:
                filters = symbol_data.get("filters", [])
                for filt in filters:
                    if filt.get("filterType") == "NOTIONAL":
                        try:
                            min_notional = float(filt.get("minNotional"))
                            logger.info("Found minNotional=%.8f for symbol %s on network.", min_notional, trading_pair)
                            return min_notional
                        except (TypeError, ValueError) as e:
                            logger.error("Invalid minNotional value for symbol %s: %s", trading_pair, e)
                            raise ValueError(
                                f"Invalid minNotional value for symbol {trading_pair}: {filt.get('minNotional')}")
                raise ValueError(f"NOTIONAL filter not found for symbol {trading_pair}.")
        raise ValueError(f"Symbol {trading_pair} not found in market info.")

    def get_min_withdrawal_quote_amount_high_liquidity(self, network: str, arb_order: ArbitrageOrder) -> float:
        """
        Retrieves the minimum withdrawal amount for the specified network by calling get_coin_info.

        The coin info contains a "networkList", where each item is a dictionary with keys such as "network"
        and "withdrawMin". This method searches for an entry in "networkList" matching the provided network
        (case-insensitive) and returns the value of "withdrawMin" as a float.

        :param network: The network identifier (e.g., "eth").
        :param arb_order: ArbitrageOrder object with the quote currency info.
        :return: The minimum withdrawal amount for the network as a float.
        :raises ValueError: If the specified network is not found or if the "withdrawMin" value cannot be parsed.
        """
        # Retrieve coin info (assumes get_coin_info is implemented elsewhere in the class)
        quote_currency = arb_order.quote_currency
        coin_info: Dict[str, Any] = self.exchange_high_liquidity.get_coin_info(quote_currency)  # TODO: Revisar esto, se cambio el metodo
        network_list: List[Dict[str, Any]] = coin_info.get("networkList", [])

        for net in network_list:
            if net.get("network", "") == network.upper():
                try:
                    withdraw_min = float(net.get("withdrawMin", 0))
                    return withdraw_min
                except (TypeError, ValueError) as e:
                    logger.error("Invalid withdrawMin value for network '%s': %s", network, e)
                    raise ValueError(f"Invalid withdrawMin value for network '{network}': {net.get('withdrawMin')}")

        raise ValueError(f"Network '{network}' not found in coin info.")

    def _set_fee_values(self, arb_order: ArbitrageOrder) -> None:
        self.low_liquidity_taker_fee: float = self.get_low_liquidity_taker_fee(arb_order)
        self.minimum_notional_low_liquidity: float = self.get_min_notional_low_liquidity(arb_order)
        self.minimum_notional_high_liquidity: float = self.get_min_notional_high_liquidity(arb_order)
        self.minimum_withdrawal_amount_quote_high_liquidity: float = \
            self.get_min_withdrawal_quote_amount_high_liquidity(
                network=self.quote_currency_network,
                arb_order=arb_order
            )

    def run_arbitrage_flow(
            self,
            arb_orders: Union[ArbitrageOrder, List[ArbitrageOrder]],
            mode: str = "infinite_loop",
            debug_mode: bool = True,
            sleep_interval: float = 0.8
    ) -> None:
        """
        Execute the arbitrage flow using REST calls to fetch the high-liquidity price.
        The flow is:

         1) Attempt to retrieve high-liquidity price (REST).
         2) Call get_price_difference => (p_diff, reference_price).
         3) If p_diff is large enough (optional threshold check), then:
            a) split_order_into_suborders => sub_orders
            b) place_sub_orders => place_result
            c) if success, check if the entire order is completed:
               - if yes => funds_transfer => reset or create new order
               - if no => place_sub_order_cancellations => confirm_cancellations => re-check next iteration
         4) Sleep a bit, or exit if mode=='single_cycle'.

        :param arb_orders: The ArbitrageOrder describing order_type, amounts, etc.
        :param mode: 'infinite_loop' or 'single_cycle'. If 'single_cycle', we do one iteration then exit.
        :param debug_mode: Boolean to specify if we are in debug mode, turn on/off the UI feature.
        :param sleep_interval: Seconds to sleep if no price or after each iteration.
        :return: None. Blocks or loops until user stops or single cycle completes.
        """
        logger.info("Starting arbitrage flow with REST-based price retrieval. mode=%s", mode)
        if not isinstance(arb_orders, list):
            arb_orders: List[ArbitrageOrder] = [arb_orders]

        base_currency: str = arb_orders[0].base_currency
        quote_currency: str = arb_orders[0].quote_currency
        if self.websocket_mode:
            # WEBSOCKET Connections
            #  Order Book:
            self.exchange_low_liquidity.connect_to_order_book(base_currency, quote_currency)
            #  Order States:
            self.exchange_low_liquidity.connect_to_order_states()
        # Set relevant attributes:
        self._set_fee_values(arb_orders[0])

        first_iteration: bool = True
        # Start the UI in a separate thread if debug_mode is off
        if not debug_mode:
            ui_thread = threading.Thread(target=self.ui.display_ui, args=(arb_orders,))
            ui_thread.daemon = True  # Ensures it ends when the main program ends
            ui_thread.start()

        if debug_mode:
            total_time = 0  # to accumulate total time for all iterations
            num_iterations = 0  # to count the number of iterations

        while True:

            try:
                start_time = time.time()
                # -------------------------------- ARBITRAGE FLOW ---------------------------------

                # 1) Get the high-liquidity price with retry mechanism
                high_liquidity_price = self._get_latest_high_liquidity_price(arb_order=arb_orders[0])

                if high_liquidity_price is None:
                    logger.debug("No valid price from REST. Sleeping for %.1fs", sleep_interval)
                    time.sleep(sleep_interval)
                    if mode == "single_cycle":
                        break
                    continue

                # 2) Compute price difference
                self.get_price_reference(high_liquidity_price, arb_orders)

                # 2.1) If it is not the first iteration, cancel orders placed in the previous iteration
                if not first_iteration:
                    # Not completed => Cancel sub-orders
                    time.sleep(sleep_interval)

                    self.place_sub_order_cancellations(sub_orders, arb_orders)
                    self.arbitrage_order_completion(arb_orders)
                    for arb_order in arb_orders:
                        if arb_order.order_completed:
                            # If fully done => funds_transfer
                            success_transfer = self.funds_transfer(arb_order)
                            if success_transfer:
                                logger.info("Funds transferred successfully. Reset order or create a new one.")
                                arb_order.reset_values(arb_order.order_completed)
                                first_iteration: bool = True
                            else:
                                logger.warning("Funds transfer failed. Evaluate partial scenario.")

                # ----------------------------- USER INTERFACE COMMANDS ---------------------------------

                # Check the shared stop flag from UI
                if self.ui.get_stop_requested():
                    logger.info("Stop command detected in main arbitrage flow. Exiting.")
                    break
                # If pause is requested, wait until it is cleared
                while self.ui.get_pause_requested():
                    logger.info("Arbitrage flow paused. Waiting to continue...")
                    time.sleep(1)
                    if self.ui.get_stop_requested():
                        logger.info("Stop command detected during pause. Exiting.")
                        return

                # ----------------------------- END USER INTERFACE COMMANDS ---------------------------------

                # 3) Split sub-orders
                sub_orders_price = self.split_order_into_suborders(arb_orders)

                if isinstance(sub_orders_price, dict) and "code" in sub_orders_price:
                    logger.error("place_sub_orders failed: %s", sub_orders_price)
                    # If the overall order amount is below the minimum, exit the arbitrage flow.
                    if sub_orders_price.get("code") == "ERROR_BELOW_MIN_TOTAL":
                        logger.error(
                            "Order amount is below the minimum allowed by the exchange. Exiting arbitrage flow.")
                        break
                    if mode == "single_cycle":
                        break
                    time.sleep(sleep_interval)
                    continue

                # 4) Place sub-orders
                sub_orders = self.place_sub_orders(arb_orders)

                if isinstance(sub_orders, dict) and "error_code" in sub_orders:
                    logger.error("place_sub_orders failed: %s", sub_orders)
                    if mode == "single_cycle":
                        break
                    continue

                # 5) Check completion
                self.arbitrage_order_completion(arb_orders)
                for arb_order in arb_orders:
                    completed_order: List[ArbitrageOrder] = []
                    if arb_order.order_completed:
                        # completed_order.append()  # TODO: Complete this logic to do multiple transfers at once
                        # If fully done => funds_transfer
                        success_transfer = self.funds_transfer(arb_order)
                        if success_transfer:
                            logger.info("Funds transferred successfully. Reset order or create a new one.")
                            arb_order.reset_values(arb_order.order_completed)
                            first_iteration: bool = True
                        else:
                            logger.warning("Funds transfer failed. Evaluate partial scenario.")
                    else:
                        first_iteration: bool = False

            except Exception as e:
                logger.error(f"An error occurred: {e}")
                # In case of an error, send an alert
                order_info = arb_orders[0].get_arbitrage_order_info()
                error_message = f""" An error occurred in arbitrage flow: \n{str(e)} 
                \nOrder info: \n{json.dumps(order_info, indent=2)}
                \nArbitrage loop was stopped.
                """
                logger.error(error_message)

                # Now call the asynchronous alert function
                asyncio.run(self.telegram_alert.send_error_alert(error_message))

                # Optionally, sleep or exit after sending an alert
                # Optionally, send an alert here (via email, Slack, etc.)
                time.sleep(sleep_interval)
                break

            # 6) Break if single cycle
            if mode == "single_cycle":
                break

            # 7) Otherwise, loop again
            logger.debug("Waiting %.1fs before next iteration...", sleep_interval)
            time.sleep(sleep_interval)

            if debug_mode:
                end_time = time.time()  # End the timer for the current loop iteration
                loop_time = end_time - start_time  # Time for this iteration
                # Update total time and iteration count
                total_time += loop_time
                num_iterations += 1
                average_time = total_time / num_iterations if num_iterations > 0 else 0
                print(f"Iteration time: {loop_time:.4f} seconds")
                print(f"Average time per iteration: {average_time:.4f} seconds")

        logger.info("Arbitrage flow ended. mode=%s", mode)

    def get_low_liquidity_taker_fee(self, arb_order: ArbitrageOrder) -> float:
        """
        Get the taker fee in the low_liquidity exchange
        :param arb_order: The ArbitrageOrder with the base and quote currency
        :return: Float representing the taker fee in the low_liquidity exchange
        """
        market_info: Dict = \
            self.exchange_low_liquidity.get_market_info(
                arb_order.base_currency,
                arb_order.quote_currency
            ).get("market", {})

        return float(market_info.get("taker_fee", 0.8)) / 100

    def register_trade_event(
            self,
            arb_order: ArbitrageOrder,
            executed_low_liq: float,
            executed_high_liq: float
    ) -> None:
        """
        Register a trade event.
        Store it into UI's attribute `trade_events`, so it can be processed and displayed.

        :param arb_order: The ArbitrageOrder describing order_type, amounts, etc.
        :param executed_low_liq: The traded amount in the low liquidity exchange.
        :param executed_high_liq: The traded amount in the low high exchange.

        """

        trade_event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "order_type": str(arb_order.order_type.name),
            "price_difference": arb_order.price_difference,
            "profit": arb_order.profit.amount,
            "traded_low": executed_low_liq,
            "traded_high": executed_high_liq,
            "low_price": arb_order.low_liquidity_price,
            "high_price": arb_order.high_liquidity_price
        }
        self.ui.trade_events.put(trade_event)

    @staticmethod
    def _create_exchange(exchange_name: str) -> Type[BinanceProxy or BudaProxy]:
        """
        Factory method to create exchange instances based on the exchange name.

        :param exchange_name: The name of the exchange (e.g., 'binance', 'buda').
        :return: The exchange class instance.
        :raises ValueError: If an unsupported exchange is provided.
        """
        return ExchangeFactory.get_exchange(exchange_name)

    def get_min_notional_low_liquidity(self, arb_order: ArbitrageOrder) -> float:
        """
        Retrieve the minimum amount for the current market (base_currency-quote_currency).

        :param arb_order: The `ArbitrageOrder` with attributes `base_currency` and `quote_currency`.
        :return: The minimum amount required by this market.
        """
        base_currency: str = arb_order.base_currency
        quote_currency: str = arb_order.quote_currency
        market_name = f"{base_currency}-{quote_currency}"
        market_info = self.exchange_low_liquidity.get_market_info(base_currency, quote_currency).get("market")
        if market_info.get("id") == market_name:
            min_amt = float(market_info.get("minimum_order_amount")[0])
            return min_amt

        # If not found, decide how to handle: raise an error or default to 0
        raise ValueError(f"No minimum amount configured for market {market_name}")

    def _get_latest_high_liquidity_price(self, arb_order: ArbitrageOrder) -> float:
        """
        Returns the `base_currency` price in expressed in `quote_currency`.
        The market symbol is constructed based on the attributes `base_currency` and `quote_currency` of an
        `ArbitrageOrder` object.

        :param arb_order: The `ArbitrageOrder` with attributes `base_currency` and `quote_currency`.
        :return: A float number representing the requested price
        """
        base_currency, quote_currency = arb_order.base_currency, arb_order.quote_currency

        price_info = self.exchange_high_liquidity.get_price(base_currency=base_currency, quote_currency=quote_currency)
        price = float(price_info.get('price'))
        return price

    def filter_order_levels(
            self,
            levels: List[List[str]],
            arb_order: ArbitrageOrder,
            high_liquidity_price: float,
            min_volume: float = 0.02,
            reverse: bool = False
    ) -> Optional[float]:
        """
        Filters a list of order book levels to find the price at which the cumulative volume
        meets or exceeds a minimum threshold.

        :param levels: A list of levels, where each level is [price, amount] as strings.
        :param arb_order: An `ArbotrageOrder` object storing the OrderType and original_amount to trade.
        :param high_liquidity_price: The limit asset price in the high liquidity exchange.
        :param min_volume: The minimum cumulative volume required.
        :param reverse: If True, process levels in descending order (for bids); otherwise, ascending (for asks).
        :return: The price (as float) at which the cumulative volume threshold is met, or None if not found.
        """
        cumulative_volume = 0.0
        # Sort levels: ascending for asks, descending for bids.
        sorted_levels = sorted(levels, key=lambda x: float(x[0]), reverse=reverse)
        min_volume = arb_order.original_amount * min_volume / float(sorted_levels[0][0])
        for level in sorted_levels:
            try:
                price = float(level[0])
                volume = float(level[1])
            except (ValueError, IndexError) as e:
                logger.error("Error parsing level data %s: %s", level, e)
                continue

            price_difference = self._calculate_real_price_diff(arb_order, price, high_liquidity_price)
            cumulative_volume += volume

            # Prevent the creation of non-profitable market orders
            if price_difference > self.price_diff_threshold:
                if price_difference >= self.low_liquidity_taker_fee + self.price_diff_threshold:
                    return price  # Creation of profitable market order
                else:
                        if arb_order.order_type is OrderType.SELL_LIMIT:
                            return price * ((1 + 0.001) / (1 + self.price_diff_threshold))
                        elif arb_order.order_type is OrderType.BUY_LIMIT:
                            return price * ((1 - 0.001) / (1 - self.price_diff_threshold))

            elif cumulative_volume >= min_volume:
                return price

        return None

    # TODO: LA LOGICA DEBE TENER EN CUENTA BUY_MARKET Y SELL_MARKET, hasta ahora solo es valida para las otras ordenes
    def get_price_reference(
            self,
            high_liquidity_price: float,
            arb_orders: Union[ArbitrageOrder, List[ArbitrageOrder]]
    ) -> Union[Tuple[float, float], List[Tuple[float, float]]]:
        """
        Retrieve the order book from the low-liquidity exchange, filter the levels to ensure that the
        cumulative volume meets a minimum threshold, and compute a price difference (%) relative to
        the high_liquidity_price.

        For BUY orders, the filtered price is derived from the bids
        (using the highest bid that meets the volume threshold).
        For SELL orders, the filtered price is derived from the asks
        (using the lowest ask that meets the volume threshold).

        :param high_liquidity_price: The asset price on the high-liquidity exchange (float).
        :param arb_orders: The `ArbitrageOrder` instance or a list of instances describing the operation type.
        :return: A tuple (p_diff, price_reference) where p_diff is the price difference in decimal form (e.g., 0.05 = 5%)
                 and price_reference is the filtered price level from the low-liquidity exchange, or a list of such tuples
                 if multiple orders are provided.
        :raises RuntimeError: If the order book data is missing/invalid or if no price level meets the volume threshold.
        """
        if isinstance(arb_orders, list):
            results = []
            for arb_order in arb_orders:
                p_diff, price_reference = self._get_price_reference_single_order(high_liquidity_price, arb_order)
                arb_order.update_price_reference(price_reference)  # Store the price reference in the order
                results.append((p_diff, price_reference))
            return results
        else:
            p_diff, price_reference = self._get_price_reference_single_order(high_liquidity_price, arb_orders)
            arb_orders.update_price_reference(price_reference)  # Store the price reference in the order
            return p_diff, price_reference

    def _get_price_reference_single_order(self, high_liquidity_price: float, arb_order: ArbitrageOrder) \
            -> Tuple[float, float]:
        """
        Helper function to handle the price reference logic for a single arbitrage order.

        :param high_liquidity_price: The asset price on the high-liquidity exchange (float).
        :param arb_order: The `ArbitrageOrder` instance describing the operation type.
        :return: A tuple (p_diff, price_reference) where p_diff is the price difference in decimal form and
                 price_reference is the filtered price level from the low-liquidity exchange.
        :raises RuntimeError: If the order book data is missing/invalid or if no price level meets the volume threshold.
        """
        logger.info(
            "Computing price difference with high_liquidity_price=%.6f for order_type=%s",
            high_liquidity_price, arb_order.order_type.name
        )
        base_currency, quote_currency = arb_order.base_currency, arb_order.quote_currency
        # 1) Fetch the order book from the low-liquidity exchange
        if not self.websocket_mode:
            response_data: Dict[str, Any] = self.exchange_low_liquidity.get_order_book(base_currency, quote_currency)
        else:
            response_data: Dict[str, Any] = self.exchange_low_liquidity.get_current_order_book()

        if "order_book" not in response_data or not response_data["order_book"]:
            raise RuntimeError("Missing 'order_book' in low-liquidity response.")
        order_book = response_data["order_book"]

        asks = order_book.get("asks", [])
        bids = order_book.get("bids", [])

        if not asks or not bids:
            raise RuntimeError("Order book is missing asks/bids data.")

        # 2) Convert all asks/bids to floats, ensuring positivity
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
        # The important value here is price_reference, not virtual_p_diff
        # TODO: Adaptar a BUY_MARKET y SELL_MARKET
        order_type_name = arb_order.order_type
        if order_type_name in [OrderType.BUY_LIMIT, OrderType.BUY_MARKET]:
            # p_diff = (high_liquidity_price - lowest_exchange_lowest_ask) / lowest_exchange_lowest_ask
            filtered_lowest_ask = self.filter_order_levels(asks, arb_order, high_liquidity_price, reverse=False)
            price_reference = min([filtered_lowest_ask, high_liquidity_price])
            low_liquidity_price = lowest_ask if order_type_name is OrderType.BUY_MARKET else \
                highest_bid
            virtual_p_diff = (high_liquidity_price - low_liquidity_price) / low_liquidity_price
        elif order_type_name in [OrderType.SELL_LIMIT, OrderType.SELL_MARKET]:
            # p_diff = (lowest_exchange_highest_bid - high_liquidity_price) / high_liquidity_price
            filtered_highest_bid = self.filter_order_levels(bids, arb_order, high_liquidity_price, reverse=True)
            price_reference = max([filtered_highest_bid, high_liquidity_price])
            low_liquidity_price = highest_bid if order_type_name is OrderType.SELL_MARKET else \
                lowest_ask
            virtual_p_diff = (low_liquidity_price - high_liquidity_price) / high_liquidity_price
        else:
            logger.error("Unrecognized order type for price diff: %s", order_type_name)
            return 0.0, 0.0  # or raise an exception

        logger.info(
            "Computed price diff=%.4f for order_type=%s (lowest_ask=%.4f, highest_bid=%.4f, high_price=%.4f)",
            virtual_p_diff, order_type_name, lowest_ask, highest_bid, high_liquidity_price
        )

        arb_order.update_market_data(
            price_diff=virtual_p_diff,
            low_liquidity_price=low_liquidity_price,
            high_liquidity_price=high_liquidity_price
        )
        return virtual_p_diff, price_reference

    def _enforce_minimum_amounts(self, sub_orders: List[Dict[str, Any]], side: str, arb_order: ArbitrageOrder) -> Any:
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
        :param arb_order: The `ArbitrageOrder` with attributes `base_currency` and `quote_currency`.
        :return: A list of valid sub-orders or an error dict.
        """
        min_required = self.minimum_notional_low_liquidity

        # WARNING: THIS IS BEING CALCULATED USING BASE CURRENCY, BCS, `min_required` is in BASE CURRENCY
        total_amount = sum(so["order"]["amount"] for so in sub_orders)
        if total_amount < min_required:
            logger.warning(
                "Total order amount %.8f is below the minimum %.8f for market %s",
                total_amount, min_required, f"{arb_order.base_currency}-{arb_order.quote_currency}"
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
            # WARNING: THIS IS BEING CALCULATED USING BASE CURRENCY, BCS, `min_required` is in BASE CURRENCY
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

    # TODO: HACER LA LOGICA MAS GENERAL CUANDO SE INCORPOREN MAS LOW LIQUIDITY EXCHANGES
    def split_order_into_suborders(self, arb_orders: Union[ArbitrageOrder, List[ArbitrageOrder]],
                                   delta: Optional[float] = None) -> Union[Any, List[Any]]:
        """
        Splits the given ArbitrageOrder's original amount into multiple sub-orders for one or more ArbitrageOrder instances.

        :param arb_orders: A single ArbitrageOrder or a list of ArbitrageOrder instances.
        :param delta: Optional delta to adjust the price.
        :return: A list of sub-orders or an error dictionary if any of the orders have an amount below the minimum allowed.
        """
        if isinstance(arb_orders, list):
            results = []
            for arb_order in arb_orders:
                result = self._split_order_for_single(arb_order, delta)
                if isinstance(result, dict) and "code" in result and result["code"] == "ERROR_BELOW_MIN_TOTAL":
                    logger.error("Order amount below minimum for %s: %s", arb_order, result)
                    return result  # Return early on failure for any order in the list
                arb_order.update_sub_orders_info(result)
                results.append(result)

            return results  # Return the list of sub-orders for all valid orders

        result = self._split_order_for_single(arb_orders, delta)
        arb_orders.update_sub_orders_info(result)
        return result # Handle single order

    def _split_order_for_single(
            self,
            arb_order: ArbitrageOrder,
            delta: Optional[float] = None
    ) -> Any:
        """
        Split the given `ArbitrageOrder`'s original_amount into multiple sub-orders,
        calculating prices based on `reference_price`.

        :param arb_order: An `ArbitrageOrder` instance whose `original_amount` will be splitted.
        :param delta: Optional delta to adjust the price.
        :return: A list of sub-orders (dicts).
        """
        reference_price: float = arb_order.price_reference
        logger.info("Splitting order into sub-orders: order=%s, reference_price=%s, side=%s, delta=%s",
                    arb_order, reference_price, arb_order.order_type.name, delta)

        order_amount = arb_order.pending_amount_low_liquidity
        sub_orders_info = [{}, {}, {}]
        # Calculate base price depending on side and delta
        order_type_name = arb_order.order_type
        if order_type_name in [OrderType.SELL_LIMIT, OrderType.SELL_MARKET]:
            side = 'ask'
            increase_factor = 1 + self.price_diff_threshold
            if delta is not None:
                increase_factor += delta
            sub_order_one_price = reference_price * increase_factor
            sub_order_two_price = sub_order_one_price * 1.001
            sub_order_three_price = sub_order_one_price * 1.002

        elif order_type_name in [OrderType.BUY_LIMIT, OrderType.BUY_MARKET]:
            side = 'bid'
            reduction_factor = 1 - self.price_diff_threshold
            if delta is not None:
                reduction_factor -= delta
            sub_order_one_price = reference_price * reduction_factor
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
        sub_orders_info[0]["amount"] = sub_order_one_amount / sub_order_one_price
        sub_orders_info[1]["amount"] = sub_order_two_amount / sub_order_two_price
        sub_orders_info[2]["amount"] = sub_order_three_amount / sub_order_three_price

        # Construct the orders structure
        market_name = f"{arb_order.base_currency}-{arb_order.quote_currency}"

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
        result = self._enforce_minimum_amounts(sub_orders, side, arb_order)

        # If result is a dict with 'code', we treat it as an error
        if isinstance(result, dict) and "code" in result:
            logger.error("Enforcing min amounts failed: %s", result)
            return result

        logger.info("Created sub-orders after enforcing min amounts: %s", result)
        return result

    def place_sub_orders(self, arb_orders: Union[ArbitrageOrder, List[ArbitrageOrder]]) -> \
            Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Place a batch of sub-orders on the low-liquidity exchange and handle partial or complete success,
        as well as common errors. Also wait for sub-orders that are in 'received' state to transition
        to another state (e.g. 'pending', 'canceled', etc.) before returning.

        :param arb_orders: A single ArbitrageOrder or a list of ArbitrageOrder instances.
        :return:
            - On success (partial or complete), a list of sub-order responses in standardized format
            - On failure, a dictionary with "error_code" and "message" (and possibly "details").
        """

        if isinstance(arb_orders, list):
            sub_orders_prices: List[Dict[str, Any]] = []
            for arb_order in arb_orders:
                sub_orders_prices += arb_order.sub_orders_info
        else:
            sub_orders_prices: List[Dict[str, Any]] = arb_orders.sub_orders_info

        logger.info("Placing sub-orders on low-liquidity exchange: %s", sub_orders_prices)
        try:
            # Place the sub-orders on the exchange
            standardized_response = self.exchange_low_liquidity.batch_creation(sub_orders_prices)

            # Update arb_orders `sub_orders_ids` attribute
            self._assign_order_ids(arb_orders, standardized_response)
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
                self._wait_for_orders_to_leave_received(received_orders, arb_orders)

            return standardized_response

        except Exception as e:
            # Catch unexpected issues such as network errors
            logger.error("Failed to place sub-orders on exchange: %s", e, exc_info=True)
            return {
                "error_code": "EXCHANGE_HTTP_ERROR",
                "message": str(e)
            }

    @staticmethod
    def _assign_order_ids(
            arb_orders: Union[ArbitrageOrder, List[ArbitrageOrder]],
            standardized_response: List[Dict[str, Any]]
    ) -> None:
        """
        For one or more ArbitrageOrder objects, match each sub-order (found in sub_orders_info)
        with a standardized order (from standardized_response) using the 'limit' value (and order type)
        and update the ArbitrageOrder attribute sub_orders_ids with the corresponding order id.

        Args:
            arb_orders: A single ArbitrageOrder or list of ArbitrageOrder objects.
            standardized_response: A list of dictionaries containing standardized order responses.
        """
        # Ensure arb_orders is a list
        if not isinstance(arb_orders, list):
            arb_orders = [arb_orders]

        # Keep track of standardized responses already used for a match
        used_indices = set()

        for arb_order in arb_orders:
            for sub_order in arb_order.sub_orders_info:
                # Extract order details from sub_order_info
                order_details: Dict = sub_order.get('order', {})
                limit_value: str = order_details.get('limit')
                order_type: str = order_details.get('type', '').lower()  # e.g., "ask" or "bid"

                matched = False
                for idx, std_order in enumerate(standardized_response):
                    if idx in used_indices:
                        continue

                    # Standardized response has a "limit" field in the form [limit_value_str, currency]
                    std_limit_list = std_order.get('limit', [])
                    if not std_limit_list or std_limit_list[0] is None:
                        continue
                    try:
                        std_limit = float(std_limit_list[0])
                    except (ValueError, TypeError):
                        continue

                    # Check if the limits match (within a small tolerance) and the order type matches.
                    if abs(limit_value - std_limit) < 1e-6 and std_order.get('type', '').lower() == order_type:
                        arb_order.sub_orders_ids.append(std_order['id'])
                        used_indices.add(idx)
                        matched = True
                        break  # Found a match for this sub order; move to the next one.
                if not matched:
                    # Optionally, log or handle the case where no matching standardized order is found.
                    pass

    def place_sub_order_cancellations(
            self,
            sub_orders: List[Dict[str, Any]],
            arb_orders: ArbitrageOrder,
    ) -> List[Dict[str, Any]]:
        """
        Cancel a batch of sub-orders on the low-liquidity exchange. If any sub-order transitions to
        'canceled_and_traded' (or partial traded states), the ArbitrageOrder object is updated accordingly.

        :param sub_orders: A list of sub-order dicts from a SUCCESSFUL place_sub_orders call,
                           each presumably with an 'id' to identify the order on the exchange.
        :param arb_orders: A single ArbitrageOrder or list of ArbitrageOrder objects to be updated if partial/traded
        took place during cancellation.
        :return: A list of sub-order dicts summarizing the cancellation operations (mode='cancel', order_id=...).
        """
        logger.info("Cancelling sub-orders on low-liquidity exchange: %s", sub_orders)
        if not isinstance(arb_orders, list):
            arb_orders = [arb_orders]

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

        if not self.websocket_mode:
            states_response = self.exchange_low_liquidity.get_order_states(
                arb_orders[0].base_currency,
                arb_orders[0].quote_currency)
        else:
            states_response: Dict[str, List[Dict[str, Any]]] = self.exchange_low_liquidity.get_current_order_states()
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
                limit_price = float(st.get("limit", 0.0)[0])
                for arb_order in arb_orders:
                    if st_id in arb_order.sub_orders_ids:
                        paid_fee_base_currency, paid_fee_quote_currency = \
                            self._calculate_paid_fee_low_liquidity(st, arb_order)

                        self._update_arbitrage_order_on_fill(
                            sub_order_dict=so,
                            new_state=st_state,
                            traded_base_amount=base_currency_traded_amount,
                            traded_quote_amount=quote_currency_traded_amount,
                            paid_fee_base_currency=paid_fee_base_currency,
                            paid_fee_quote_currency=paid_fee_quote_currency,
                            limit_price_low_liquidity=limit_price,
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
    def _calculate_paid_fee_low_liquidity(order_state: Dict[str, str], arb_order: ArbitrageOrder) -> float:
        """
        Uses the information of `order_state` and returns the paid fee expressed in the quote currency of
        `ArbitrageOrder`.
        WARNING: Currently only works for Buda responses.

        :param order_state: state of a traded order.
        :param arb_order: An ArbitrageOrder object with the quote currency information
        :return: Tuple[float, float] representing the paid fee expressed in base and quote currencies
        """
        quote_currency = arb_order.quote_currency
        paid_fee_info = order_state.get("paid_fee", [0, quote_currency])
        paid_fee: float = float(paid_fee_info[0])
        paid_fee_currency: str = paid_fee_info[1]
        limit_price = float(order_state.get("limit", 0)[0])

        if paid_fee_currency.upper() == quote_currency:
            paid_fee_quote_currency = paid_fee
            paid_fee_base_currency = paid_fee_quote_currency / limit_price

            return paid_fee_base_currency, paid_fee_quote_currency

        elif paid_fee_currency.upper() == arb_order.base_currency:
            paid_fee_base_currency = paid_fee
            paid_fee_quote_currency = limit_price * paid_fee
            return paid_fee_base_currency, paid_fee_quote_currency
        else:
            logger.error("paid_fee_currency does not belong to base or quote currency of ArbitrageBot, "
                         "instead: {}".format(paid_fee_currency))
            return 0, 0

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

    def _wait_for_orders_to_leave_received(
            self,
            received_orders: List[Dict[str, Any]],
            arb_orders: Union[ArbitrageOrder, List[ArbitrageOrder]],
            max_wait_seconds: int = 30
    ) -> None:
        """
        Wait for sub-orders in 'received' state to transition to another state.
        If the sub-order transitions to a traded-related state, update `arb_order` dynamic amounts.

        :param received_orders: The sub-order responses that are in 'received' state.
        :param arb_orders: A single ArbitrageOrder or list of ArbitrageOrder objects to be updated with partial/traded
        amounts.
        :param max_wait_seconds: How long to keep polling before giving up.
        :return: None (updates the sub-orders in-place, updates `arb_order` amounts).
        """
        logger.info("Waiting for %d sub-orders to transition out of 'received'...", len(received_orders))
        start_time = time.time()

        if not isinstance(arb_orders, list):
            arb_orders = [arb_orders]

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
                # break SE QUEDA EN UN LOOP INFINITO

            # Sleep briefly
            time.sleep(0.2)

            # 1. Retrieve updated states from the exchange
            if not self.websocket_mode:
                states_response = self.exchange_low_liquidity.get_order_states(
                    arb_orders[0].base_currency,
                    arb_orders[0].quote_currency
                )
            else:
                states_response: Dict[str, List[Dict[str, Any]]] = self.exchange_low_liquidity.get_current_order_states()
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
                            if st_state == 'pending':
                                continue
                            # Potentially the exchange server might return a 'traded_amount' field or similar
                            # to indicate how much was actually traded in this sub-order fill.
                            # We'll fetch that and update `arb_order`.
                            base_currency_traded_amount = float(st.get("traded_amount", 0.0)[0])
                            quote_currency_traded_amount = float(st.get("total_exchanged", 0.0)[0])
                            limit_price = float(st.get("limit", 0.0)[0])

                            for arb_order in arb_orders:
                                if st_id in arb_order.sub_orders_ids:
                                    paid_fee_base_currency, paid_fee_quote_currency = \
                                        self._calculate_paid_fee_low_liquidity(st, arb_order)
                                    self._update_arbitrage_order_on_fill(
                                        sub_order_dict=ro,
                                        new_state=st_state,
                                        traded_base_amount=base_currency_traded_amount,
                                        traded_quote_amount=quote_currency_traded_amount,
                                        paid_fee_base_currency=paid_fee_base_currency,
                                        paid_fee_quote_currency=paid_fee_quote_currency,
                                        limit_price_low_liquidity=limit_price,
                                        arb_order=arb_order
                                    )

                    # Remove from 'received_ids'
                    received_ids.remove(st_id)

            if not received_ids:
                logger.info("All 'received' sub-orders transitioned to another state.")
                break

    def _update_arbitrage_order_on_fill(self,
                                        sub_order_dict: Dict[str, Any],
                                        new_state: str,
                                        traded_base_amount: float,
                                        traded_quote_amount: float,
                                        paid_fee_base_currency: float,
                                        paid_fee_quote_currency: float,
                                        limit_price_low_liquidity: float,
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
        :param paid_fee_base_currency: The paid fee expressed in the base currency
        :param paid_fee_quote_currency: The paid fee expressed in the quote currency
        :param limit_price_low_liquidity: The limit price in the low liquidity exchange
        :param arb_order: The ArbitrageOrder object to update.
        """

        traded_amount = traded_quote_amount  # The traded amount is expressed in quote_currency, bcs usually it is FIAT
        if new_state in ("traded", "canceled_and_traded", "pending", 'canceled') and traded_amount > 0:
            logger.info(
                "Sub-order %s changed state to %s with traded_amount=%.4f. Updating ArbitrageOrder.",
                sub_order_dict.get("id"), new_state, traded_amount
            )
            # Increase the traded_amount_low_liquidity
            # Recompute pending_amount_low_liquidity = original_amount - traded_amount_low_liquidity
            # Update the pending amount to trade in the high liquidity exchange
            arb_order.update_low_liquidity_traded(traded_quote_delta=traded_quote_amount,
                                                  traded_base_delta=traded_base_amount,
                                                  paid_fee_base_currency=paid_fee_base_currency,
                                                  paid_fee_quote_currency=paid_fee_quote_currency)
            # If partial, we keep trying. If fully filled, we might see if pending_amount is close to zero.
            self.execute_opposite_order_high_liquidity_exchange(arb_order, limit_price_low_liquidity)

        else:
            logger.info(
                "Sub-order %s changed state to %s with no fill update. (traded_amount=%.4f)",
                sub_order_dict.get("id"), new_state, traded_amount
            )
        # Possibly add more logic if new_state = 'canceled' or 'pending', etc.

    def execute_opposite_order_high_liquidity_exchange(self, arb_order: 'ArbitrageOrder',
                                                       limit_price_low_liquidity: float) \
            -> Union[Dict[str, Any], Dict[str, Any]]:
        """
        Synchronously place a MARKET order on the high-liquidity exchange for the
        arb_order.pending_amount_high_liquidity, then call arb_order.fulfill_high_liquidity(...)
        with the executed quantity.
        When the order is successfully traded, it updates the ArbitrageOrder instance via its
        `update_market_data` method and then pushes this information to the UI.


        :param arb_order: The ArbitrageOrder object to update.
        :param limit_price_low_liquidity: The limit price in the low liquidity exchange
        """

        init_amount_to_trade_low_liq: float = arb_order.get_pending_quote_amount_high_liquidity

        to_trade_quote_currency = arb_order.get_pending_quote_amount_high_liquidity
        to_trade_base_currency = arb_order.get_pending_base_amount_high_liquidity  # Pending amount, in base currency
        min_notional_factor: float = 1.15  # Increasing factor to avoid "code":-1013 (MIN NOTIONAL) error due rounding

        if arb_order.order_type in [OrderType.BUY_LIMIT, OrderType.BUY_MARKET]:
            side = "SELL"
        elif arb_order.order_type in [OrderType.SELL_LIMIT, OrderType.SELL_MARKET]:
            side = "BUY"
        if to_trade_quote_currency <= self.minimum_notional_high_liquidity * min_notional_factor:
            logger.info("No pending amount to trade in the high-liquidity side.")
            return {"msg": "No pending amount to trade."}

        logger.info("Placing MARKET order on high-liquidity exchange: side=%s, qty=%.4f", side, to_trade_quote_currency)
        try:
            if self.currency_of_interest == CurrencyOfInterest.QUOTE:  # Want to accumulate quote currency
                order_resp = self.exchange_high_liquidity.new_order(
                    base_currency=arb_order.base_currency,
                    quote_currency=arb_order.quote_currency,
                    side=side.upper(),
                    order_type='MARKET',
                    quantity=round(Decimal(to_trade_base_currency), 5),  # Amount expressed in base currency
                )
            elif self.currency_of_interest == CurrencyOfInterest.BASE:  # Want to accumulate base currency
                order_resp = self.exchange_high_liquidity.new_order(
                    base_currency=arb_order.base_currency,
                    quote_currency=arb_order.quote_currency,
                    side=side.upper(),  # Must be either `SELL` or `BUY`
                    order_type='MARKET',
                    quote_order_qty=to_trade_quote_currency,  # Amount expressed in quote currency
                )

            if "code" in order_resp and order_resp["code"] < 0:
                logger.error("High-liquidity exchange error: %s", order_resp)
                return order_resp

            executed_base_qty = float(order_resp.get("executedQty", 0.0))
            limit_price_high_liquidity = float(order_resp.get("fills", [0.0])[0].get("price", 0.0))
            executed_quote_qty = round(executed_base_qty * limit_price_high_liquidity, 5)

            # Turn it back to quote currency
            paid_fee_base_currency, paid_fee_quote_currency = \
                self._calculate_paid_fee_high_liquidity(order_resp, arb_order)
            arb_order.fulfill_high_liquidity(
                executed_quote_qty,
                executed_base_qty,
                paid_fee_base_currency,
                paid_fee_quote_currency
            )

            price_difference = self._calculate_real_price_diff(
                arb_order,
                limit_low_liquidity=limit_price_low_liquidity,
                limit_high_liquidity=limit_price_high_liquidity
            )

            # Update arb_order: `ArbitrageOrder`
            arb_order.update_profit(
                price_difference=price_difference)  # TODO: se puede hacer metodo privado y encapsularlo en fulfull_high_liquidity
            arb_order.update_market_data(
                price_diff=price_difference,
                low_liquidity_price=limit_price_low_liquidity,
                high_liquidity_price=limit_price_high_liquidity
            )

            # Update the UI
            self.register_trade_event(arb_order, init_amount_to_trade_low_liq, executed_quote_qty)
            return order_resp

        except Exception as e:
            current_method_name = inspect.currentframe().f_code.co_name
            logger.error(f"{current_method_name} - Error from Binance: {e}")
            raise

    @staticmethod
    def _calculate_real_price_diff(arb_order: ArbitrageOrder, limit_low_liquidity: float, limit_high_liquidity: float) \
            -> float:
        """
        Calculate the real price difference of the executed orders in both exchanges.
        Real price difference means the price difference calculated with the real execution limit prices.

        :param arb_order: The `ArbitrageOrder` describing the operation type (BUY or SELL).
        :param limit_low_liquidity: Limit price of trade execution in the low liquidity exchange.
        :param limit_high_liquidity: Limit price of trade execution in the high liquidity exchange.
        :return: Float representing the price difference
        """

        order_type = arb_order.order_type
        if order_type in [OrderType.BUY_LIMIT, OrderType.BUY_MARKET]:
            p_diff = (limit_high_liquidity - limit_low_liquidity) / limit_low_liquidity
            return p_diff
        elif order_type in [OrderType.SELL_LIMIT, OrderType.SELL_MARKET]:
            p_diff = (limit_low_liquidity - limit_high_liquidity) / limit_high_liquidity
            return p_diff
        else:
            logger.error("Wrong OrderType: {}".format(order_type))
            return 0.0

    @staticmethod
    def _calculate_paid_fee_high_liquidity(order_state: Dict[str, str], arb_order: ArbitrageOrder) \
            -> Tuple[float, float]:
        """
        Uses the information of `order_state` and returns the paid fee in the high liquidity exchange expressed in both
         base and quote currencies of `ArbitrageOrder`.
        WARNING: Currently only works for BINANCE responses.

        :param order_state: state of a traded order.
        :param arb_order: An ArbitrageOrder object with the quote currency information
        :return: Tuple[float, float] representing the paid fee expressed in base and quote currencies
        """
        quote_currency = arb_order.quote_currency
        trade_info: Dict[str, Any] = order_state.get('fills', [{}])[0]

        paid_fee: float = float(trade_info.get("commission", 0))
        paid_fee_currency: str = trade_info.get("commissionAsset", "")

        limit_price = float(trade_info.get("price", 0))

        if paid_fee_currency.upper() == quote_currency:
            paid_fee_quote_currency = paid_fee
            paid_fee_base_currency = paid_fee_quote_currency / limit_price

            return paid_fee_base_currency, paid_fee_quote_currency
        elif paid_fee_currency.upper() == arb_order.base_currency:
            paid_fee_base_currency = paid_fee
            paid_fee_quote_currency = limit_price * paid_fee
            return paid_fee_base_currency, paid_fee_quote_currency

        else:
            logger.error("paid_fee_currency does not belong to base or quote currency of ArbitrageBot, "
                         "instead: {}".format(paid_fee_currency))
            return 0, 0

    def funds_transfer(self, arb_orders: Union['ArbitrageOrder', List['ArbitrageOrder']]) -> bool:
        """
        Execute both btc_transfer and quote_currency_transfer for one or more ArbitrageOrder instances in parallel.
        For each order, the two transfers are executed concurrently. Returns True only if all transfers for all orders succeed.

        :param arb_orders: A single ArbitrageOrder or a list of ArbitrageOrder objects, each containing the relevant
                           traded amounts and order type.
        :return: True if funds transfers for all orders succeed, False otherwise.
        """
        # Ensure arb_orders is a list
        if not isinstance(arb_orders, list):
            arb_orders = [arb_orders]

        overall_success = True
        order_futures = {}
        # Launch a thread for each order's funds transfer
        with ThreadPoolExecutor(max_workers=len(arb_orders)) as order_executor:
            for order in arb_orders:
                future = order_executor.submit(self._funds_transfer_single, order)
                order_futures[order] = future

            for order, future in order_futures.items():
                try:
                    success = future.result()
                    if not success:
                        overall_success = False
                except Exception as e:
                    logger.error("Error transferring funds for order %s: %s", order, e)
                    overall_success = False

        return overall_success

    def _funds_transfer_single(self, arb_order: 'ArbitrageOrder') -> bool:
        """
        Execute both btc_transfer and quote_currency_transfer concurrently for a single ArbitrageOrder.

        :param arb_order: An ArbitrageOrder instance.
        :return: True if both transfers succeed, False otherwise.
        """
        logger.info("Initiating parallel funds transfer for order_type=%s", arb_order.order_type.name)

        def do_btc_transfer() -> bool:
            logger.debug("Starting btc_transfer for order %s...", arb_order)
            return self.btc_transfer(arb_order)

        def do_quote_transfer() -> bool:
            logger.debug("Starting quote_currency_transfer for order %s...", arb_order)
            return self.quote_currency_transfer(arb_order)

        # Use two threads: one for BTC, one for quote currency
        with ThreadPoolExecutor(max_workers=2) as executor:
            btc_future = executor.submit(do_btc_transfer)
            quote_future = executor.submit(do_quote_transfer)
            btc_success = btc_future.result()
            quote_success = quote_future.result()

        if btc_success and quote_success:
            logger.info("All funds transferred successfully (BTC + quote) for order %s", arb_order)
            arb_order.reset_values(order_completion=True)
            return True
        else:
            logger.warning("Some transfers failed for order %s: btc_success=%s, quote_success=%s", arb_order,
                           btc_success, quote_success)
            return False

    def arbitrage_order_completion(self, arb_orders: Union[ArbitrageOrder, List[ArbitrageOrder]]) -> bool:
        """
        Checks if an arbitrage order has been completed. This is True when ArbitrageOrder's attribute
        `traded_quote_amount_low_liquidity` is larger or equal than the 98.5 % of `original_amount` attribute.
        It is not exactly equal, because of fees and rounding errors.

        :param arb_orders: The ArbitrageOrder to check.
        :return: Boolean value defining the completion state of the order
        """

        if not isinstance(arb_orders, list):
            arb_orders = [arb_orders]

        for arb_order in arb_orders:
            reference_price: float = arb_order.price_reference
            min_notional_low_liquidity_quote = self.minimum_notional_low_liquidity * reference_price * 1.1

            arb_order.order_completed: bool = arb_order.traded_quote_amount_low_liquidity \
                                              >= (arb_order.original_amount - min_notional_low_liquidity_quote)

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
        if isinstance(sender, BaseHighLiquidityExchange):
            if total_quote_currency <= self.minimum_withdrawal_amount_quote_high_liquidity:
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
    def _wait_for_asset_withdraw(coin: str, sender: Any, withdraw_id: str, max_wait_seconds: int = 60 * 10) -> bool:
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
            if state == 'Awaiting Approval':
                continue
            elif state not in ("pending_confirmation", "confirmed", 'executing', ''):
                logger.error(
                    "Withdrawal ID=%s entered unexpected state=%s. Stopping.",
                    withdraw_id, state
                )
                return False
