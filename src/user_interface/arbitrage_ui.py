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
    Handles the terminal-based UI for the arbitrage bot, including a dynamic table and progress visualization.
    Also listens for user commands (stop/pause/continue) to control the arbitrage flow.
    """

    def __init__(self):
        self.console = Console()
        self.table = Table(title="Arbitrage Order Status")
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=True
        )
        self.progress_task = self.progress.add_task("Order Progress", total=100)
        self._stop_requested: bool = False
        self._pause_requested: bool = False
        self.lock = threading.Lock()
        # We'll hold a reference to the latest arbitrage order for UI updates
        self.arb_order: Optional[ArbitrageOrder] = None

        # Setup table columns
        self.table.add_column("Timestamp", justify="right", style="cyan")
        self.table.add_column("Order Type", justify="center", style="green")
        self.table.add_column("Price Difference", justify="center", style="magenta")
        self.table.add_column("Profit", justify="center", style="bold yellow")
        self.table.add_column("Traded (Low Liquidity)", justify="center", style="blue")
        self.table.add_column("Traded (High Liquidity)", justify="center", style="blue")
        self.table.add_column("Low Liquidity Price", justify="center", style="cyan")
        self.table.add_column("High Liquidity Price", justify="center", style="cyan")
        self.table.add_column("Pending (High Liquidity)", justify="center", style="red")

    def listen_for_commands(self) -> None:
        """
        Listens for user commands to control the arbitrage process:
            - 's' or 'stop' to stop the bot.
            - 'p' or 'pause' to pause the bot.
            - 'c' or 'continue' to resume if paused.
        This method blocks and should run in a separate thread.
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

    def update_table(self, arb_order: ArbitrageOrder) -> None:
        """
        Updates the UI table with the latest information from the ArbitrageOrder.

        :param arb_order: The current ArbitrageOrder containing updated order status and trading data.
        """
        # Clear and rebuild the table for each update
        self.table = Table(title="Arbitrage Order Status")
        self.table.add_column("Timestamp", justify="right", style="cyan")
        self.table.add_column("Order Type", justify="center", style="green")
        self.table.add_column("Price Difference", justify="center", style="magenta")
        self.table.add_column("Profit", justify="center", style="bold yellow")
        self.table.add_column("Traded (Low Liquidity)", justify="center", style="blue")
        self.table.add_column("Traded (High Liquidity)", justify="center", style="blue")
        self.table.add_column("Low Liquidity Price", justify="center", style="cyan")
        self.table.add_column("High Liquidity Price", justify="center", style="cyan")
        self.table.add_column("Pending (High Liquidity)", justify="center", style="red")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.table.add_row(
            timestamp,
            str(arb_order.order_type),
            f"{arb_order.price_difference * 100:.2f}%",
            f"{arb_order.profit.amount:.2f} {arb_order.profit.currency}",
            f"{arb_order.traded_base_amount_low_liquidity:.2f} {arb_order.base_currency}",
            f"{arb_order.traded_amount_base_high_liquidity:.2f} {arb_order.base_currency}",
            f"{arb_order.low_liquidity_price:.2f}",
            f"{arb_order.high_liquidity_price:.2f}",
            f"{(arb_order._pending_quote_amount_high_liquidity + arb_order._pending_base_amount_high_liquidity):.2f}"
        )
        self.console.clear()
        self.console.print(self.table)

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
            f"Progress: {completed:.2f} / {total:.2f} {arb_order.quote_currency} traded.",
            title="Arbitrage Progress",
        )
        self.console.print(progress_info)
        self.console.print(self.progress)

    def display_ui(self, arb_order: ArbitrageOrder) -> None:
        """
        Starts the UI display and command listener in a loop.
        The UI is updated every second and reflects both the current arbitrage data and user commands.

        :param arb_order: The current ArbitrageOrder instance.
        """
        # Set the initial order for shared access
        with self.lock:
            self.arb_order = arb_order

        # Start the command listener in a separate thread
        command_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        command_thread.start()

        while True:
            time.sleep(1)  # Update every second
            with self.lock:
                # Check for stop request
                if self._stop_requested:
                    self.console.print("[bold red]Stop command detected. Exiting UI...[/bold red]")
                    break

                # Display updates only if not paused
                if not self._pause_requested:
                    self.update_table(arb_order)
                    self.update_progress(arb_order)

        # Clear the arb_order reference when stopping UI
        with self.lock:
            self.arb_order = None

