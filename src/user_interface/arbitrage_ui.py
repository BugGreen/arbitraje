from src.exchange_api.low_liquidity_exchanges.base_low_liquidity_exchange import BaseLowLiquidityExchange
from src.exchange_api.high_liquidity_exchanges.base_high_liquidity_exchange import BaseHighLiquidityExchange
from src.order_types.encoders import OrderType, CurrencyOfInterest
from src.order_types.arbitrage_order import ArbitrageOrder
from rich.progress import Progress, BarColumn, TextColumn
from typing import Optional, List, Dict, Any, Tuple
from src.user_interface import encoders
from rich.console import Console
from rich.prompt import Confirm
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
import threading
import logging
import queue
import time

logger = logging.getLogger(__name__)


class ArbitrageUI:
    """
    Handles the terminal-based UI for the arbitrage bot.

    The UI has two main sections:
      1. Market Data Panel: Updates every second with live market data.
      2. Trade History Table: A log that appends a new row each time a trade occurs.

    The UI also listens for user commands (stop/pause/continue) to control the bot.
    """

    def __init__(self):
        self.console = Console()

        # Panel for live market data
        self.market_data_panel = Panel("")

        # Progress bar for arbitrage orders progress
        self.progress_one = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
        )
        self.progress_task_one = self.progress_one.add_task("Order Progress", total=100)

        self.progress_two = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
        )
        self.progress_task_two = self.progress_two.add_task("Order Progress", total=100)

        # Control flags for UI/flow
        self._stop_requested: bool = False
        self._pause_requested: bool = False
        self.lock = threading.Lock()

        # Shared arbitrage order (set by main flow)
        self.arb_order: Optional[ArbitrageOrder] = None

        # Trade events queue (to capture trade records as they occur)
        self.trade_events: "queue.Queue[Dict[str, Any]]" = queue.Queue()

    @staticmethod
    def create_trade_record_table_placeholder(arb_order: ArbitrageOrder) -> Table:
        """
        Create an empty trade history table.

        :param arb_order: The current ArbitrageOrder.
        :return: The Trades History table.
        """
        trade_history_table = Table(title="Trade History")
        trade_history_table.add_column("Timestamp", justify="right", style="cyan")
        trade_history_table.add_column("Order Type", justify="center", style="green")
        trade_history_table.add_column("Price Diff (%)", justify="center", style="magenta")
        trade_history_table.add_column("Profit", justify="center", style="bold yellow")
        trade_history_table.add_column(f"Traded ({arb_order.low_liquidity_exchange})", justify="center", style="blue")
        trade_history_table.add_column(f"Traded ({arb_order.high_liquidity_exchange})", justify="center", style="blue")
        trade_history_table.add_column(f"{arb_order.low_liquidity_exchange} Price", justify="center", style="cyan")
        trade_history_table.add_column(f"{arb_order.high_liquidity_exchange} Price", justify="center", style="cyan")
        return trade_history_table

    @staticmethod
    def append_trade_record(history_table: Table, trade_record: Dict[str, Any]) -> None:
        """
        Append a new trade record to the trade history table.

        :param history_table: The Trade History table.
        :param trade_record: A dictionary with keys: 'timestamp', 'order_type', 'price_difference',
                             'profit', 'traded_low', 'traded_high', 'low_price', 'high_price'.
        """
        history_table.add_row(
            trade_record.get("timestamp", ""),
            trade_record.get("order_type", ""),
            f"{trade_record.get('price_difference', 0) * 100:.2f}%",
            f"{trade_record.get('profit', 0):.2f}",
            f"{trade_record.get('traded_low', 0):.2f}",
            f"{trade_record.get('traded_high', 0):.2f}",
            f"{trade_record.get('low_price', 0):.2f}",
            f"{trade_record.get('high_price', 0):.2f}"
        )

    def process_trade_events(self, trade_history_table: Table) -> None:
        """
        Process trade events from the trade_events queue and update the trade history table.

        :param trade_history_table: Table History Table to update
        """
        while not self.trade_events.empty():
            event = self.trade_events.get()
            self.append_trade_record(trade_history_table, event)

    def update_market_data(self, arb_order: ArbitrageOrder) -> None:
        """
        Update the market data panel with the latest market information.

        :param arb_order: The current ArbitrageOrder containing market data attributes.
        """
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Price Diff (%)", justify="center")
        table.add_column(f"{arb_order.low_liquidity_exchange} Price", justify="center")
        table.add_column(f"{arb_order.high_liquidity_exchange} Price", justify="center")
        table.add_column("Progress (%)", justify="center")

        progress = \
            ((arb_order.original_amount - arb_order.pending_amount_low_liquidity) / arb_order.original_amount) * 100 \
                if arb_order.original_amount > 0 else 0.0

        table.add_row(
            f"{arb_order.price_difference * 100:.2f}%",
            f"{arb_order.low_liquidity_price:.2f}",
            f"{arb_order.high_liquidity_price:.2f}",
            f"{progress:.2f}%"
        )
        self.market_data_panel = Panel(table, title="Market Data")
        self.console.print(self.market_data_panel)

    def update_progress(self, arb_order: ArbitrageOrder, progress: Progress, progress_task) -> None:
        """
        Update the progress bar to show the arbitrage order completion progress.

        :param arb_order: The ArbitrageOrder from which to compute progress.
        """
        total = arb_order.original_amount
        completed = arb_order.original_amount - arb_order.pending_amount_low_liquidity
        progress_percentage = (completed / total) * 100 if total > 0 else 0.0
        progress.update(progress_task, completed=progress_percentage)
        progress_panel = Panel(progress, title=f"{arb_order.order_type.name} No. {arb_order.order_number}",
                               subtitle=f"{completed:.2f} of {total:.2f} {arb_order.quote_currency} traded.")
        self.console.print(progress_panel)

    def display_ui(self, arb_orders: List[ArbitrageOrder]) -> None:
        """
        Continuously update the UI with market data and trade history, and listen for user commands.
        Market data and progress are updated every second; trade history is updated whenever new trade events occur.

        :param arb_orders: The current ArbitrageOrder instance.
        """

        trade_history_table: Table = self.create_trade_record_table_placeholder(arb_orders[0])

        with self.lock:
            self.arb_order = arb_orders

        # Start the command listener in a separate thread.
        command_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        command_thread.start()

        while True:
            time.sleep(1)  # Update market data every second
            with self.lock:
                if self._stop_requested:
                    self.console.print("[bold red]Stop command detected. Exiting UI...[/bold red]")
                    break
                if not self._pause_requested:
                    self.console.clear()
                    # Update market data panel and progress bar
                    self.update_market_data(arb_orders[0])

                    # Process trade events and update trade history table
                    self.process_trade_events(trade_history_table)
                    self.console.print(trade_history_table)
                    if len(arb_orders) == 2:
                        self.update_progress(arb_orders[0], self.progress_one, self.progress_task_one)
                        self.update_progress(arb_orders[1], self.progress_two, self.progress_task_two)
                    else:
                        self.update_progress(arb_orders[0], self.progress_one, self.progress_task_one)
                    self.console.print(
                        "Enter command (s: stop or p: pause).")

        with self.lock:
            self.arb_order = None

    def listen_for_commands(self) -> None:
        """
        Listen for user commands to control the arbitrage process:
          - 's' or 'stop': Stop the bot.
          - 'p' or 'pause': Pause the bot.
          - 'c' or 'continue': Resume the bot if paused.
        Runs in its own thread.
        """
        self.console.print(
            "[bold yellow]Command Listener:[/bold yellow] Type 's' (stop), 'p' (pause), or 'c' (continue).")
        while True:
            command = input("Enter command (s: stop, p: pause, c: continue): ").strip().lower()
            with self.lock:
                if command in ("s", "stop"):
                    self._stop_requested = True
                    self.console.print("[bold red]Stop command received.[/bold red]")
                    break
                elif command in ("p", "pause"):
                    self._pause_requested = True
                    self.console.print("[bold yellow]Pause command received.[/bold yellow]")
                elif command in ("c", "continue"):
                    self._pause_requested = False
                    self.console.print("[bold green]Continue command received.[/bold green]")
                else:
                    self.console.print(
                        "[bold red]Unrecognized command.[/bold red] Valid commands: s (stop), p (pause), c (continue).")

    def get_stop_requested(self):
        return self._stop_requested

    def get_pause_requested(self):
        return self._pause_requested


def welcome_menu() -> None:
    """
    Displays the welcome menu that prompts the user to enter the parameters to initialize the arbitrage bot.
    """
    from src.arbitrage_bot.arbitrage_bot import ArbitrageBot

    market_values: Dict[str, Any] = encoders.market_values
    console = Console()

    console.print("[bold cyan]Welcome to the Arbitrage Bot Setup[/bold cyan]", style="bold green")
    # display_initiation_values_table(initialization_values, console, default_values_mode=True)
    #
    # default_values = Confirm.ask("Do you want to use the default values?")

    arb_bot: ArbitrageBot = create_arb_bot_object(console, market_values)
    order_side: str = market_values.get("Side", "")
    market: str = market_values.get("Market", "BTC-USDC")
    mode: str = market_values.get("Mode")
    arb_orders: List[ArbitrageOrder] = create_arb_orders(console, mode=mode, side=order_side, market=market)

    frozen_amounts: bool = display_balances(arb_bot, arb_orders[0], console)

    if frozen_amounts:
        cancel_orders = Confirm.ask("Do you want to cancel the frozen amounts?")
        if cancel_orders:

            cancel_all_orders(arb_bot, arb_orders[0])
            display_balances(arb_bot, arb_orders[0], console)
            continue_with_current_balance = Confirm.ask("This is your current Balance, do you want to continue?")
            if not continue_with_current_balance:
                welcome_menu()
    else:
        continue_with_current_balance = Confirm.ask("This is your current Balance, do you want to continue?")
        if not continue_with_current_balance:
            welcome_menu()

    # Start the arbitrage flow
    arb_bot.run_arbitrage_flow(arb_orders=arb_orders)


def set_market_initialization_values(console: Console, market_initiation_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Change the market initialization values via input

    :param console: Console object from Rich
    :param market_initiation_values: Dict containing the market initialization values
    :return: Dict with the modified initialization values
    """
    console.print("Please define the following parameters to begin.")

    # Market Symbol
    market_symbol: str = Prompt.ask(
        "Select the market",
        choices=["BTC-USDC"],  # Example list, modify as needed.initialization_values'
        default="BTC-USDC"
    )
    market_initiation_values["Market"] = market_symbol
    display_initiation_values_table(market_initiation_values, console)

    # High Liquidity Exchange
    exchange_high = Prompt.ask(
        "Select the high liquidity exchange",
        choices=["binance"],  # Example list, modify as needed
        default="binance"
    )
    market_initiation_values["E. High Liquidity"] = exchange_high
    display_initiation_values_table(market_initiation_values, console)

    # Low Liquidity Exchange
    exchange_low = Prompt.ask(
        "Select low liquidity exchange",
        choices=["buda"],  # Example list, modify as needed
        default="buda"
    )
    market_initiation_values["E. Low Liquidity"] = exchange_low
    display_initiation_values_table(market_initiation_values, console)

    # Price Difference Threshold
    price_diff_threshold: float = float(Prompt.ask(
        "Enter price difference threshold (e.g., 0.4)",
        default=0.4)
    )
    market_initiation_values["P. Difference"] = price_diff_threshold
    display_initiation_values_table(market_initiation_values, console)

    # Mode
    mode = Prompt.ask(
        "Enter trading mode 0: 'ONE_SIDE' 1: 'BOTH_SIDES'",
        choices=["0", "1"],
        default="0"
    )
    if mode == "0":
        market_initiation_values["Mode"] = "ONE_SIDE"
        # SIDE
        side = Prompt.ask(
            "Enter the trading side 0: 'SELL_LIMIT' 1: 'BUY_LIMIT'",
            choices=["0", "1"],
            default="0"
        )
        market_initiation_values["Side"] = 'SELL_LIMIT' if side == "0" else "BUY_LIMIT"
    else:
        market_initiation_values["Mode"] = "BOTH_SIDES"
        del market_initiation_values["Side"]

    display_initiation_values_table(market_initiation_values, console)

    return market_initiation_values


def create_arb_bot_object(console: Console, market_initiation_values: [str, Any]) -> "ArbitrageBot":

    from src.arbitrage_bot.arbitrage_bot import ArbitrageBot

    display_initiation_values_table(market_initiation_values, console, default_values_mode=True)
    default_values = Confirm.ask("Do you want to use the Market values?")
    market_initiation_values: Dict[str, Any] = market_initiation_values if default_values \
        else set_market_initialization_values(console, market_initiation_values)

    market_symbol: List[str] = market_initiation_values.get("Market", "BTC-USDC").split("-")
    base_currency: str = market_symbol[0]
    quote_currency: str = market_symbol[1]

    arb_bot: ArbitrageBot = ArbitrageBot(
        exchange_high_liquidity=market_initiation_values.get("E. High Liquidity"),
        exchange_low_liquidity=market_initiation_values.get("E. Low Liquidity"),
        price_diff_threshold=market_initiation_values.get("P. Difference"),
        base_currency=base_currency,
        quote_currency=quote_currency,
    )

    return arb_bot


def cancel_all_orders(bot: "ArbitrageBot", arb_order: ArbitrageOrder) -> None:
    """
    Cancel all pending orders in a marker with symbol base_currency-quote_currency.

    :param bot: ArbitrageBot object with the exchanges' information.
    :param arb_order:  ArbitrageOrder with the base and quote currency info.
    """
    low_liquidity_exchange: BaseLowLiquidityExchange = bot.exchange_low_liquidity
    base_currency: str = arb_order.base_currency
    quote_currency: str = arb_order.quote_currency

    low_liquidity_exchange.cancel_all_orders(base_currency, quote_currency)


def create_balances_table(bot: "ArbitrageBot", arb_order: ArbitrageOrder) -> Tuple[Table, bool]:
    """
    Create a rich.Table object to display the current balance in the low liquidity exchanfe for a given base-quote
    currency market.

    :param bot: ArbitrageBot object with the exchanges' information.
    :param arb_order:  ArbitrageOrder with the base and quote currency info.
    :return: Tuple a Table with the balance information, and a boolean representing the presence of frozen amount.
    """
    balances_table = Table(title="Balances")

    balances_table.add_column("Currency", justify="center", style="bold", no_wrap=True)
    balances_table.add_column("Amount", justify="center", style="cyan")
    balances_table.add_column("Available Amount", justify="center", style="green")
    balances_table.add_column("Frozen Amount", justify="center", style="red")

    balances_table, frozen_amounts = append_balance_values(balances_table, bot, arb_order)

    return balances_table, frozen_amounts


def append_balance_values(balances_table: Table, bot: "ArbitrageBot", arb_order: ArbitrageOrder) -> Tuple[Table, bool]:
    """
    Populate the rich.Table object to display the current balance in the low liquidity exchange for a given base-quote
    currency market.

    :param bot: ArbitrageBot object with the exchanges' information.
    :param arb_order:  ArbitrageOrder with the base and quote currency info.
    :return: Tuple a Table with the balance information, and a boolean representing the presence of frozen amount.
    """

    low_liquidity_exchange: BaseLowLiquidityExchange = bot.exchange_low_liquidity
    high_liquidity_exchange: BaseHighLiquidityExchange = bot.exchange_high_liquidity
    base_currency: str = arb_order.base_currency
    quote_currency: str = arb_order.quote_currency

    low_liquidity_balances: Dict[str, List] = low_liquidity_exchange.get_balances().get('balances')

    new_row = list()
    frozen_amount_bool: bool = False

    for balance in low_liquidity_balances:
        currency_id = balance['id']
        if currency_id in [base_currency, quote_currency]:
            total_amount: float = round(float(balance['amount'][0]), 6)
            available_amount: float = round(float(balance['available_amount'][0]), 6)
            frozen_amount: float = round(float(balance['frozen_amount'][0]), 6)

            new_row.append("{:,}".format(total_amount))
            new_row.append("{:,}".format(available_amount))
            new_row.append("{:,}".format(frozen_amount))
            balances_table.add_row(currency_id, new_row[0], new_row[1], new_row[2])

            frozen_amount_bool: bool = bool(frozen_amount) if not frozen_amount_bool else frozen_amount_bool

        new_row = list()

    return balances_table, frozen_amount_bool


def display_balances(bot: "ArbitrageBot", arb_order: ArbitrageOrder, console: Console) -> bool:
    """
    Display the current balances in the low liquidity exchange.

    :param bot: ArbitrageBot object with the exchanges' information.
    :param arb_order:  ArbitrageOrder with the base and quote currency info.
    :param console: rich.Console object.
    :return: Boolean, True if there is a frozen amount that can be cancelled.
    """
    balances_table, frozen_amounts = create_balances_table(bot, arb_order)
    console.print(balances_table)
    return frozen_amounts


def create_initiation_values(default_values_mode: bool = True) -> Table:
    """
    Create a rich.Table object to display the initialization values to be used,

    :param default_values_mode: Boolean, True if the default values will be used
    :return: Table with the initialization values
    """

    title: str = "Initiation Default Values" if default_values_mode else "Initiation Values"
    initiation_values_table = Table(title=title)
    initiation_values_table.add_column("Parameter", justify="left", style="cyan")
    initiation_values_table.add_column("Value", justify="left", style="green")

    return initiation_values_table


def append_initiation_values(initiation_values_table: Table, initiation_values: Dict[str, Any]) -> None:
    """
    Append a new trade record to the trade history table.

    :param initiation_values_table: The Trade History table.
    :param initiation_values: A dictionary with keys: 'E. High Liquidity', 'E. Low Liquidity', 'P. Difference',
                         'Base Currency', 'Quote Currency', 'Amount', 'Mode'.
    """
    for attr, value in initiation_values.items():
        if isinstance(value, (float, int)):
            value = f"{value:.2f}"
        initiation_values_table.add_row(attr, value)


def one_side_order_creation(
        console: Console,
        market: str = "BTC-USDC"
) -> ArbitrageOrder:

    arb_order_one_side_default: Dict[str, Any] = encoders.arb_oder_sell_limit_values
    display_initiation_values_table(arb_order_one_side_default, console, default_values_mode=True)
    default_values = Confirm.ask(f"Do you want to use the default Arbitrage Order values?")

    if default_values:

        market_symbol: List[str] = market.split("-")
        base_currency: str = market_symbol[0]
        quote_currency: str = market_symbol[1]
        currency_of_interest: CurrencyOfInterest = CurrencyOfInterest.QUOTE if \
            arb_order_one_side_default.get("Quote Currency") == "QUOTE" else CurrencyOfInterest.BASE
        order_type: OrderType = OrderType.SELL_LIMIT if \
            arb_order_one_side_default.get("Order Type") == "SELL_LIMIT" else OrderType.BUY_LIMIT

        arb_order: ArbitrageOrder = ArbitrageOrder(
            base_currency=base_currency,
            quote_currency=quote_currency,
            original_amount=arb_order_one_side_default.get("Amount"),
            currency_of_interest=currency_of_interest,
            order_type=order_type,
            sub_orders_num=arb_order_one_side_default.get("Sub-orders amount", 1)
        )
    else:
        order_type: str = Prompt.ask(
            "Select the side 0: 'SELL_LIMIT' 1: 'BUY_LIMIT'",
            choices=["0", "1"],
            default="0"
        )
        sub_orders_amount: int = int(Prompt.ask(
            "Select the number of sub orders to create (max 3):",
            choices=["1", "2", "3"],  # Example list, modify as needed
            default="2"
        ))
        order_type: OrderType = OrderType.SELL_LIMIT if order_type == "0" else OrderType.BUY_LIMIT
        arb_order_init_values: Dict[str, Any] = encoders.arb_oder_sell_limit_values if \
            order_type is OrderType.SELL_LIMIT else encoders.arb_oder_buy_limit_values
        arb_order_init_values["Sub-orders amount"] = sub_orders_amount
        arb_order: ArbitrageOrder = create_arb_order(console, arb_order_init_values, market)

    return arb_order


def create_arb_orders(console: Console, mode: str, side: str, market: str = "BTC-USDC") -> List[ArbitrageOrder]:
    arb_orders: List[ArbitrageOrder] = []

    ones_side_mode: bool = True if mode == "ONE_SIDE" else False
    if ones_side_mode:
        one_side_order: ArbitrageOrder = one_side_order_creation(console, market)
        arb_orders.append(one_side_order)
    else:
        for order_type in encoders.arb_orders_values.values():
            arb_order: ArbitrageOrder = create_arb_order(console, order_type, market)
            arb_orders.append(arb_order)

    return arb_orders


def create_arb_order(
        console: Console,
        arb_order_initiation_values: Dict[str, Any],
        market: str
) -> ArbitrageOrder:

    display_initiation_values_table(arb_order_initiation_values, console, default_values_mode=True)
    order_type: str = arb_order_initiation_values.get("Order Type", "SELL_LIMIT")
    default_values = Confirm.ask(f"Do you want to use the default Arbitrage Order values ({order_type})?")
    arb_order_initiation_values: Dict[str, Any] = arb_order_initiation_values if default_values \
        else set_arb_order_initialization_values(console, arb_order_initiation_values)

    market_symbol: List[str] = market.split("-")
    base_currency: str = market_symbol[0]
    quote_currency: str = market_symbol[1]

    currency_of_interest: CurrencyOfInterest = CurrencyOfInterest.QUOTE if \
        arb_order_initiation_values.get("Quote Currency") == "QUOTE" else CurrencyOfInterest.BASE
    order_type: OrderType = OrderType.SELL_LIMIT if \
        arb_order_initiation_values.get("Order Type") == "SELL_LIMIT" else OrderType.BUY_LIMIT
    # Create the ArbitrageOrder with user-defined parameters
    arb_order: ArbitrageOrder = ArbitrageOrder(
        base_currency=base_currency,
        quote_currency=quote_currency,
        original_amount=arb_order_initiation_values.get("Amount"),
        currency_of_interest=currency_of_interest,
        order_type=order_type,
        sub_orders_num=arb_order_initiation_values.get("Sub-orders amount", 1)
    )

    return arb_order


def set_arb_order_initialization_values(console: Console, arb_order_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Change the Arbitrage Order initialization values via input

    :param console: Console object from Rich
    :param arb_order_values: Dict containing the Arbitrage Order initialization values
    :return: Dict with the modified initialization values
    """
    order_type: str = arb_order_values.get("Order Type", "SELL_LIMIT")
    console.print(f"Please define the Arbitrage Order [{order_type}] parameters:")

    # Amount to be traded
    original_amount = float(Prompt.ask(
        "Enter the AMOUNT to be arbitraged",
        default=2000
    ))
    arb_order_values["Amount"] = original_amount
    display_initiation_values_table(arb_order_values, console)

    # Currency to Accumulate
    currency_of_interest: str = str(Prompt.ask(
        "Select the currency to accumulate 0: 'QUOTE' 1: 'BASE'",
        choices=["0", "1"],  # Example list, modify as needed
        default="0"
    ))

    sub_orders_amount: int = int(Prompt.ask(
        "Select the number of sub orders to create (max 3):",
        choices=["1", "2", "3"],  # Example list, modify as needed
        default="2"
    ))

    arb_order_values["Currency of Interest"] = currency_of_interest
    display_initiation_values_table(arb_order_values, console)
    currency_of_interest: str = "QUOTE" if currency_of_interest == "0" else "BASE"
    arb_order_values["Currency of Interest"] = currency_of_interest
    arb_order_values["Sub-orders amount"] = sub_orders_amount

    return arb_order_values


def set_initialization_values(console: Console, initiation_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Change the initialization values via input

    :param console: Console object from Rich
    :param initiation_values: Dict containing the initialization values
    :return: Dict with the modified initialization values
    """
    console.print("Please define the following parameters to begin.")

    exchange_high = Prompt.ask(
        "Select high liquidity exchange",
        choices=["binance"],  # Example list, modify as needed
        default="binance"
    )

    initiation_values["E. High Liquidity"] = exchange_high
    display_initiation_values_table(initiation_values, console)

    exchange_low = Prompt.ask(
        "Select low liquidity exchange",
        choices=["buda"],  # Example list, modify as needed
        default="buda"
    )

    initiation_values["E. Low Liquidity"] = exchange_low
    display_initiation_values_table(initiation_values, console)

    # Prompt for price difference threshold
    price_diff_threshold = float(Prompt.ask("Enter price difference threshold (e.g., 0.4)", default=0.4))
    initiation_values["P. Difference"] = price_diff_threshold
    display_initiation_values_table(initiation_values, console)

    # Prompt for mode (e.g., 'conservative', 'aggressive')
    mode = Prompt.ask("Enter trading mode", default="conservative")
    initiation_values["Mode"] = mode
    display_initiation_values_table(initiation_values, console)

    # Prompt for base currency (e.g., BTC)
    base_currency = Prompt.ask("Enter base currency", default="BTC")
    initiation_values["Base Currency"] = base_currency
    display_initiation_values_table(initiation_values, console)

    # Prompt for quote currency (e.g., USDC)
    quote_currency = Prompt.ask("Enter quote currency", default="USDC")
    initiation_values["Quote Currency"] = quote_currency
    display_initiation_values_table(initiation_values, console)

    # Prompt for the original amount to be traded
    original_amount = float(Prompt.ask("Enter the original amount to be arbitraged", default=2000))
    initiation_values["Amount"] = original_amount

    display_initiation_values_table(initiation_values, console)

    return initiation_values


def display_initiation_values_table(
        initiation_values: Dict[str, Any],
        console: Console,
        default_values_mode: bool = False) -> None:
    """
    Display the initialization values in the console

    :param initiation_values: Dict containing the initialization values
    :param console: Console object from Rich
    :param default_values_mode: Boolean, True if the default values will be used
    """
    initiation_values_table = create_initiation_values(default_values_mode)
    append_initiation_values(initiation_values_table, initiation_values)

    console.clear()
    console.print(initiation_values_table)
