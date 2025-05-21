# ArbitrageBot Class Documentation

This document provides an overview of the **ArbitrageBot** class and its methods. The `ArbitrageBot` orchestrates 
various steps in an arbitrage workflow, including creating and canceling sub-orders on a low-liquidity exchange, 
transferring funds (BTC or quote currency) between exchanges, and synchronously executing tasks in both a sequential 
and parallel manner.

---

## Overview

The **ArbitrageBot** class encapsulates logic for:

1. **Factory creation** of the underlying exchange proxies (`BinanceProxy`, `BudaProxy`).
2. **Retrieving** market-specific data (e.g., minimal amounts).
3. **Placing / canceling** sub-orders on the low-liquidity exchange, polling for final states (e.g. `'traded'`, `'canceled'`, `'pending'`).
4. **Updating** an associated `ArbitrageOrder` object whenever sub-orders partially or fully fill.
5. **Transferring** assets (BTC or quote currency) between two exchanges, either sequentially or (optionally) in parallel.
6. **Enforcing** sub-order minimum amounts and merging sub-orders if needed.

Below is a summary of each method, including parameters and return values.

---

## Methods

### 1. `_create_exchange(exchange_name: str) -> Type[BinanceProxy or BudaProxy]`
Factory method to create exchange instances based on the exchange name.

- **Parameters**  
  - `exchange_name (str)`: The name of the exchange (e.g. `'binance'`, `'buda'`).
- **Returns**  
  - An instance of the corresponding exchange proxy (`BinanceProxy` or `BudaProxy`).
- **Raises**  
  - `ValueError` if an unsupported exchange is provided.

---

### 2. `get_min_amount_for_market() -> float`
Retrieve the minimum required amount for the current market (`base_currency-quote_currency`).

- **Parameters**  
  - *(none)*
- **Returns**  
  - A `float` representing the minimum trading amount on this market.

---

### 3. `get_price_difference() -> float`
Calculates the **price difference** between the two exchanges in percentage. (Currently **pending** further logic 
refinement.)

- **Parameters**  
  - *(none)*
- **Returns**  
  - A `float` representing the difference in percentage (e.g. 0.5 for 0.5%).

> **Note**: This method is **incomplete**; its calculation logic remains to be refined or updated based on actual 
> pricing data from each exchange.

---

### 4. `place_sub_orders(sub_orders: List[Dict[str, Any]], arb_order: ArbitrageOrder) -> Union[List[Dict[str, Any]], Dict[str, Any]]`
Places a batch of sub-orders on the **low-liquidity** exchange, then polls for final states (`'received'` → `'traded'`, `'pending'`, `'canceled'`, etc.). Updates the `ArbitrageOrder` if partial fills occur.

- **Parameters**  
  - `sub_orders (List[Dict[str, Any]])`: A list of sub-order dictionaries in a standardized format.  
  - `arb_order (ArbitrageOrder)`: An order object to be updated with partial fill amounts and statuses.
- **Returns**  
  - On success, a **list** of sub-order response dictionaries (partial or full success).
  - On failure, a **dict** containing `{"error_code": ..., "message": ...}` (or other error details).
  
---

### 5. `place_sub_order_cancellations(sub_orders: List[Dict[str, Any]], arb_order: ArbitrageOrder) -> List[Dict[str, Any]]`
Cancels a batch of sub-orders on the **low-liquidity** exchange. If any sub-order transitions to `'canceled_and_traded'` or partial states, the `ArbitrageOrder` is updated accordingly.

- **Parameters**  
  - `sub_orders (List[Dict[str, Any]])`: A list of sub-order dictionaries from a **successful** `place_sub_orders` call. Each sub-order typically has an `'id'` used to identify it.  
  - `arb_order (ArbitrageOrder)`: The order object to update if partial trades occur during cancellation.
- **Returns**  
  - A **list** describing the cancellation operations. Each entry typically has `"mode": "cancel"` and `"order_id": ...`.

---

### 6. `_handle_unprepared_or_minimum_amount_errors(sub_order_responses: Union[List[Dict[str, Any]], Dict[str, Any]]) -> Union[None, Dict[str, Any]]`
Analyzes sub-order responses for known error states (`'unprepared'`, `'insufficient_funds'`, `'amount_less_than_minimum'`, etc.).

- **Parameters**  
  - `sub_order_responses`: Either a **list** of sub-order dicts (partial success scenario) or a **dict** with a global `error_code` (e.g., `'EXCHANGE_API_ERROR_invalid_record'`).
- **Returns**  
  - `None` if **no** critical errors found.
  - A **dict** with `{"error_code": ..., "message": ...}` (and possibly `'sub_order'`) if an error is detected.

---

### 7. `_wait_for_orders_to_leave_received(received_orders: List[Dict[str, Any]], arb_order: ArbitrageOrder, max_wait_seconds: int = 10) -> None`
Polls the **low-liquidity** exchange for sub-orders in `'received'` state. Once an order transitions to `'traded'` or partial states, we call `_update_arbitrage_order_on_fill(...)` to reflect the fill amounts in `arb_order`.

- **Parameters**  
  - `received_orders (List[Dict[str, Any]])`: Sub-orders with status `'received'`.  
  - `arb_order (ArbitrageOrder)`: The order object to update upon partial or full fills.  
  - `max_wait_seconds (int)`: How long to wait before giving up. Default is `10`.

- **Returns**  
  - `None`, but updates the sub-orders in-place and modifies `arb_order`.

---

### 8. `_update_arbitrage_order_on_fill(sub_order_dict: Dict[str, Any], new_state: str, traded_base_amount: float, traded_quote_amount: float, arb_order: ArbitrageOrder) -> None`
Updates the `ArbitrageOrder` with partial fill amounts (base and quote currency) whenever a sub-order’s state changes to `'traded'` or `'partially_traded'`.

- **Parameters**  
  - `sub_order_dict (Dict[str, Any])`: The sub-order changing states.  
  - `new_state (str)`: The new sub-order state.  
  - `traded_base_amount (float)`: How much base currency was actually traded on the low-liquidity side.  
  - `traded_quote_amount (float)`: How much quote currency was traded on the low-liquidity side.  
  - `arb_order (ArbitrageOrder)`: The order object to update (accumulating partial fills, updating pending amounts, etc.).
- **Returns**  
  - `None` (updates are done in-place on `arb_order`).

---

### 9. `check_sub_orders_status(sub_order_ids: List[str]) -> Dict[dict, Any]`
Checks the status of multiple sub-orders by their IDs.

- **Parameters**  
  - `sub_order_ids (List[str])`: The IDs of sub-orders we want to query.
- **Returns**  
  - A **dict** containing sub_order details. For example, `{"orders": [{...}, {...}]}` or a structure that includes state info.

---

### 10. `execute_opposite_order_high_liquidity_exchange(arb_order: ArbitrageOrder) -> Union[Dict[str, Any], Dict[str, Any]]`
Synchronously places a **market** order on the **high-liquidity** exchange for `arb_order.pending_amount_high_liquidity`. Then calls `arb_order.fulfill_high_liquidity(...)` with the actual executed quantity.

- **Parameters**  
  - `arb_order (ArbitrageOrder)`: Contains the pending high-liquidity side amount (`pending_amount_high_liquidity`) to offset the partial fill on the low-liquidity side.
- **Returns**  
  - On success, a **dict** describing the new order or partial fill, e.g. `{ "executedQty": "0.4", "status": "FILLED" }`.  
  - On error, a **dict** containing an error code and message.

---

### 11. `split_order_into_suborders(order: ArbitrageOrder, reference_price: float, side: str, delta: Optional[float] = None) -> Any`
Splits an `ArbitrageOrder`’s `original_amount` into multiple sub-orders (e.g., 60/30/10 distribution).

- **Parameters**  
  - `order (ArbitrageOrder)`: The order whose `original_amount` is to be split.  
  - `reference_price (float)`: Base for limit price calculations.  
  - `side (str)`: `'ask'` or `'bid'`.  
  - `delta (Optional[float])`: Additional price offset.
- **Returns**  
  - A **list** of sub-orders with the structure:
    ```json
    [
      { "mode": "place", "order": {...} },
      { "mode": "place", "order": {...} },
      { "mode": "place", "order": {...} }
    ]
    ```

---

### 12. `_enforce_minimum_amounts(sub_orders: List[Dict[str, Any]], side: str) -> Any`
Ensures each sub-order meets the **market’s minimum**. If sub-orders are below minimum, merges them into a single 
“target” sub-order. If after merging, none are above the min, returns an error dict.

- **Parameters**  
  - `sub_orders (List[Dict[str, Any]])`: Sub-orders to check/merge if too small.
  - `side (str)`: `'ask'` or `'bid'`, because merging logic differs by side.
- **Returns**  
  - A **list** of valid sub-orders or a **dict** with an error code if merging or minimum enforcement fails.

---

### 13. `funds_transfer(arb_order: 'ArbitrageOrder') -> bool`
Executes **both** `btc_transfer` and `quote_currency_transfer` **in parallel**, returning `True` only if both succeed.

- **Parameters**  
  - `arb_order (ArbitrageOrder)`: Contains the amounts (BTC and quote currency) and order type.
- **Returns**  
  - `True` if both transfers succeed, `False` if either fails.

---

### 14. `btc_transfer(arb_order: ArbitrageOrder) -> bool`
Synchronously transfers BTC between exchanges (low-liquidity ↔ high-liquidity) based on the order type (buy or sell). 
It splits the total BTC if needed, creates LN invoices on the receiver, pays them from the sender, then waits for 
confirmation on the sender side.

- **Parameters**  
  - `arb_order (ArbitrageOrder)`: Must have `traded_base_amount_low_liquidity`.
- **Returns**  
  - `True` if all chunks are transferred/confirmed, `False` otherwise.

---

### 15. `quote_currency_transfer(arb_order: ArbitrageOrder) -> bool`
Synchronously transfers the **quote currency** between exchanges (opposite direction of the BTC). If `order_type` is 
in `[BUY_LIMIT, BUY_MARKET]`, it transfers from **high-liquidity** to **low-liquidity**. If `[SELL_LIMIT, SELL_MARKET]`, 
from **low-liquidity** to **high-liquidity**.

- **Parameters**  
  - `arb_order (ArbitrageOrder)`: Must have `traded_quote_amount_low_liquidity` for the total quote currency to send.
- **Returns**  
  - `True` if the quote transfer completes successfully, `False` if any step fails.

---

### 16. `_split_btc_amount(total_btc: float) -> List[float]`
Splits `total_btc` into smaller chunks for LN invoice or withdrawal constraints (e.g. if `0.017 BTC` must be `[0.009999, 0.007001]` to respect min/max rules).

- **Parameters**  
  - `total_btc (float)`: The total BTC to be broken into sub-chunks.
- **Returns**  
  - A **list** of floats, each chunk up to `MAX_BTC_PER_INVOICE` and above `MIN_BTC_PER_INVOICE` when possible.

---

## Conclusion

The **ArbitrageBot** class orchestrates **sub-order placement**, **cancellation**, **asset transfers**, and 
**order state updates**. By separating each function into clear responsibilities:

1. **Sub-Order** methods (`place_sub_orders`, `place_sub_order_cancellations`, `_wait_for_orders_to_leave_received`, etc.) handle order creation and polling on the **low-liquidity** exchange.
2. **Asset Transfer** methods (`btc_transfer`, `quote_currency_transfer`, `funds_transfer`) handle the movement of base (BTC) and quote currencies between the **two** exchanges.
3. **Utility** methods (`_handle_unprepared_or_minimum_amount_errors`, `_update_arbitrage_order_on_fill`, `_split_btc_amount`, `_enforce_minimum_amounts`) ensure error handling, partial fill updates, and sub-order minimum merges are consistent.

This framework supports a synchronous approach to **arbitrage**: you wait for each step (order creation, partial fill, 
transfer) to finish or fail, returning booleans or error codes to drive the next step in the arbitrage logic.
