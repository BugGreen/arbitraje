from typing import Dict, List, Optional

binance_deposit_states = {
    0: "pending_confirmation",
    6: "retained",
    7: "Wrong Deposit",
    8: "Waiting User confirm",
    1: "confirmed",
    2: "rejected"
}

binance_withdrawal_states = {
    0: "Email Sent",
    2: "Awaiting Approval",
    3: "rejected",
    4: "pending_confirmation",
    6: "confirmed"
}
