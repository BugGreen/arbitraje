from src.order_types.encoders import OrderType, CurrencyOfInterest
from src.order_types.arbitrage_order import ArbitrageOrder
from src.user_interface import encoders
from typing import Optional, List, Dict, Any
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Confirm
from rich.prompt import Prompt
from rich.console import Console
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

        # Progress bar for arbitrage order progress
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
        )
        self.progress_task = self.progress.add_task("Order Progress", total=100)

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

    def update_progress(self, arb_order: ArbitrageOrder) -> None:
        """
        Update the progress bar to show the arbitrage order completion progress.

        :param arb_order: The ArbitrageOrder from which to compute progress.
        """
        total = arb_order.original_amount
        completed = arb_order.original_amount - arb_order.pending_amount_low_liquidity
        progress_percentage = (completed / total) * 100 if total > 0 else 0.0
        self.progress.update(self.progress_task, completed=progress_percentage)
        progress_panel = Panel(self.progress, title="Arbitrage Progress",
                               subtitle=f"{completed:.2f} / {total:.2f} {arb_order.quote_currency} traded.")
        self.console.print(progress_panel)

    def display_ui(self, arb_order: ArbitrageOrder) -> None:
        """
        Continuously update the UI with market data and trade history, and listen for user commands.
        Market data and progress are updated every second; trade history is updated whenever new trade events occur.

        :param arb_order: The current ArbitrageOrder instance.
        """

        trade_history_table: Table = self.create_trade_record_table_placeholder(arb_order)

        with self.lock:
            self.arb_order = arb_order

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
                    self.update_market_data(arb_order)
                    self.update_progress(arb_order)
                    # Process trade events and update trade history table
                    self.process_trade_events(trade_history_table)
                    self.console.print(trade_history_table)
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

    initialization_values = encoders.initialization_values
    console = Console()

    console.print("[bold cyan]Welcome to the Arbitrage Bot Setup[/bold cyan]", style="bold green")
    display_initiation_values_table(initialization_values, console, default_values_mode=True)

    default_values = Confirm.ask("Do you want to use the default values?")

    initialization_values = initialization_values if default_values \
        else set_initialization_values(console, initialization_values)

    # Create the ArbitrageBot with user inputs
    bot = ArbitrageBot(
        exchange_high_liquidity=initialization_values.get("E. High Liquidity"),
        exchange_low_liquidity=initialization_values.get("E. Low Liquidity"),
        price_diff_threshold=initialization_values.get("P. Difference"),
        mode=initialization_values.get("Mode"),
        base_currency=initialization_values.get("Base Currency"),
        quote_currency=initialization_values.get("Quote Currency"),
    )

    # Create the ArbitrageOrder with user-defined parameters
    arb_order = ArbitrageOrder(
        base_currency=initialization_values.get("Base Currency"),
        quote_currency=initialization_values.get("Quote Currency"),
        original_amount=initialization_values.get("Amount"),
        currency_of_interest=CurrencyOfInterest.QUOTE,
        order_type=OrderType.BUY_LIMIT
    )

    # Start the arbitrage flow
    bot.run_arbitrage_flow(arb_order=arb_order)


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
