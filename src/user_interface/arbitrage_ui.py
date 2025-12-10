import threading
import time
import logging
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.panel import Panel
from typing import Optional, List, Dict, Any
from src.order_types.arbitrage_order import ArbitrageOrder

logger = logging.getLogger(__name__)


class ArbitrageUI:
    """
    Handles the terminal-based UI for the arbitrage bot.

    The UI is divided into two main sections:
      1. Market Data Panel: Updates every second with live market data.
      2. Trade History Table: Appends a new row every time a trade is executed,
         maintaining a history of trades.

    It also incorporates a command listener to allow the user to pause, continue, or stop the bot.
    """

    def __init__(self):
        self.console = Console()

        # Market Data Panel (will be updated every second)
        self.market_data_panel = Panel("")

        # Progress bar for arbitrage order progress
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
        )
        self.progress_task = self.progress.add_task("Order Progress", total=100)

        # Flags for controlling UI and flow
        self._stop_requested: bool = False
        self._pause_requested: bool = False
        self.lock = threading.Lock()

        # Shared arbitrage order for UI updates (set by main flow)
        self.arb_order: Optional["ArbitrageOrder"] = None

    def listen_for_commands(self) -> None:
        """
        Listen for user commands to control the arbitrage process:
          - 's' or 'stop': Stop the bot.
          - 'p' or 'pause': Pause the bot.
          - 'c' or 'continue': Resume the bot if paused.
        This function runs in its own thread and updates internal flags.
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

    def update_market_data(self, arb_order: "ArbitrageOrder") -> None:
        """
        Update the market data panel with the latest market information.

        :param arb_order: The current ArbitrageOrder containing market data attributes.
        """
        # Build a simple table for market data (we're not preserving history here)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Price Diff (%)", justify="center")
        table.add_column(f"{arb_order.low_liquidity_exchange} Price", justify="center")
        table.add_column(f"{arb_order.high_liquidity_exchange} Price", justify="center")
        table.add_column("Progress (%)", justify="center")

        # Calculate progress as the percentage of (original - pending_low) / original.
        progress = \
            ((arb_order.original_amount - arb_order.pending_amount_low_liquidity) / arb_order.original_amount) \
            * 100 if arb_order.original_amount > 0 else 0.0

        table.add_row(
            f"{arb_order.price_difference * 100:.2f}%",
            f"{arb_order.low_liquidity_price:.2f}",
            f"{arb_order.high_liquidity_price:.2f}",
            f"{progress:.2f}%"
        )
        self.market_data_panel = Panel(table, title="Market Data")
        # Display the market data panel
        self.console.print(self.market_data_panel)

    def update_table(self, history_table: Table, arb_order: ArbitrageOrder, update_history: bool = False) -> None:
        """
        Updates the UI table with the latest information from the ArbitrageOrder.

        :param history_table: The History Table
        :param arb_order: The current ArbitrageOrder containing updated order status and trading data.
        """
        if update_history:
            history_table = self.append_trade_record(history_table, arb_order)
        self.console.print(history_table)

    @staticmethod
    def create_trade_record_table(arb_order: ArbitrageOrder) -> Table:
        """
        Creates the Trade History Table (initially empty)
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
    def append_trade_record(history_table: Table, arb_order: "ArbitrageOrder") -> Table:
        """
        Appends a new trade record to the trade history table.

        :param history_table: The Trades History table.
        :param arb_order: The current ArbitrageOrder.
        :return: The updated Trades History table.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_table.add_row(
            timestamp,
            str(arb_order.order_type),
            f"{arb_order.price_difference * 100:.2f}%",
            f"{arb_order.profit.amount:.2f} {arb_order.profit.currency}",
            f"{arb_order.traded_base_amount_low_liquidity:.2f} {arb_order.base_currency}",
            f"{arb_order.traded_amount_base_high_liquidity:.2f} {arb_order.base_currency}",
            f"{arb_order.low_liquidity_price:.2f}",
            f"{arb_order.high_liquidity_price:.2f}",
            f"{arb_order.get_pending_quote_amount_high_liquidity:.2f}"
        )
        # Redraw the trade history table
        # self.console.print(self.trade_history_table)
        return history_table

    def update_progress(self, arb_order: ArbitrageOrder) -> None:
        """
        Updates the progress bar to reflect the completion progress of the arbitrage order.

        Progress is computed as the percentage of the low-liquidity traded amount relative to the original amount.

        :param arb_order: The ArbitrageOrder to read progress from.
        """
        total = arb_order.original_amount
        completed = arb_order.original_amount - arb_order.pending_amount_low_liquidity
        progress_percentage = (completed / total) * 100 if total > 0 else 0
        self.progress.update(self.progress_task, completed=progress_percentage)
        progress_info = Panel(
            self.progress,
            subtitle=f"Progress: {completed:.2f} / {total:.2f} {arb_order.quote_currency} traded. ",
            title="Arbitrage Progress",
        )
        self.console.print(progress_info)

    def display_ui(self, arb_order: "ArbitrageOrder") -> None:
        """
        Continuously updates the UI with market data and trade history, and listens for user commands.
        Updates the market data every second, while trade history is only appended when a new trade occurs.

        :param arb_order: The current ArbitrageOrder instance.
        """
        with self.lock:
            self.arb_order = arb_order

        # Start command listener in a separate thread.
        command_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        command_thread.start()
        history_table = self.create_trade_record_table(arb_order)

        while True:
            time.sleep(1)  # Update market data every second
            with self.lock:
                if self._stop_requested:
                    self.console.print("[bold red]Stop command detected. Exiting UI...[/bold red]")
                    break
                if not self._pause_requested:
                    self.console.clear()
                    self.update_table(history_table, arb_order, True)
                    self.update_progress(arb_order)
                    self.update_market_data(arb_order)
                    # The trade history table is updated only when append_trade_record is called by the arbitrage flow.

        with self.lock:
            self.arb_order = None

