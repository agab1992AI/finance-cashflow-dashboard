import json
from datetime import date, datetime
from pathlib import Path


DEFAULT_DATA = {
    "bank_accounts": [
        {"name": "Main account", "balance": 0.0}
    ],
    "credit_cards": [
        {
            "card_name": "Credit card",
            "credit_limit": 0.0,
            "current_balance": 0.0,
            "statement_balance": 0.0,
            "statement_date": "2026-08-01",
            "payment_due_date": "2026-08-18",
            "minimum_payment_due": 0.0,
            "amount_paid_this_statement": 0.0,
            "remaining_statement_balance": 0.0,
            "apr": 0.0,
            "promotional_apr": 0.0,
            "interest_charged": 0.0,
            "direct_debit_enabled": "No",
            "payment_status": "Not paid",
            "notes": "",
        }
    ],
    "loans": [
        {"name": "Car loan", "balance": 0.0}
    ],
    "savings": [
        {"name": "Emergency fund", "balance": 0.0}
    ],
    "investments": [
        {"name": "Portfolio", "value": 0.0}
    ],
    "monthly_income": [
        {"name": "Salary", "amount": 0.0}
    ],
    "monthly_expenses": [
        {"name": "Rent", "amount": 0.0}
    ],
    "direct_debits": [
        {"name": "Subscription", "amount": 0.0, "due_date": "2026-08-10"}
    ],
    "payments_completed": [
        {"name": "Payment", "amount": 0.0}
    ],
    "payments_pending": [
        {"name": "Pending payment", "amount": 0.0}
    ],
    "goals": [
        {"name": "Become Debt Free", "target_amount": 3500.0, "current_amount": 850.0},
        {"name": "Driving Licence", "target_amount": 1500.0, "current_amount": 0.0},
        {"name": "Emergency Fund", "target_amount": 2500.0, "current_amount": 500.0},
        {"name": "Holidays", "target_amount": 2000.0, "current_amount": 600.0},
    ],
}


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _derive_card_payment_status(statement_balance, minimum_payment_due, amount_paid_this_statement, payment_due_date):
    if statement_balance <= 0 or amount_paid_this_statement >= statement_balance:
        return "Fully paid"

    try:
        due_date = datetime.strptime(payment_due_date, "%Y-%m-%d").date()
        if due_date < date.today() and amount_paid_this_statement < minimum_payment_due:
            return "Overdue"
    except (TypeError, ValueError):
        pass

    if minimum_payment_due > 0 and amount_paid_this_statement >= minimum_payment_due:
        return "Minimum paid"

    return "Not paid"


def normalize_credit_card(item):
    card_name = _clean_text(item.get("card_name") or item.get("name") or "Credit card")
    current_balance = _to_float(item.get("current_balance", item.get("balance", 0.0)))
    statement_balance = _to_float(item.get("statement_balance", current_balance))
    minimum_payment_due = _to_float(item.get("minimum_payment_due", item.get("minimum_payment", 0.0)))
    amount_paid_this_statement = _to_float(item.get("amount_paid_this_statement", 0.0))
    remaining_statement_balance = max(statement_balance - amount_paid_this_statement, 0.0)
    payment_due_date = _clean_text(item.get("payment_due_date") or item.get("payment_date") or "2026-08-18")
    direct_debit_enabled = _clean_text(item.get("direct_debit_enabled") or item.get("direct_debit", "No"))
    if direct_debit_enabled.lower() in {"yes", "true", "y", "1"}:
        direct_debit_enabled = "Yes"
    else:
        direct_debit_enabled = "No"

    payment_status = _derive_card_payment_status(
        statement_balance,
        minimum_payment_due,
        amount_paid_this_statement,
        payment_due_date,
    )

    return {
        "card_name": card_name,
        "credit_limit": _to_float(item.get("credit_limit", 0.0)),
        "current_balance": current_balance,
        "statement_balance": statement_balance,
        "statement_date": _clean_text(item.get("statement_date") or "2026-08-01"),
        "payment_due_date": payment_due_date,
        "minimum_payment_due": minimum_payment_due,
        "amount_paid_this_statement": amount_paid_this_statement,
        "remaining_statement_balance": round(remaining_statement_balance, 2),
        "apr": _to_float(item.get("apr", 0.0)),
        "promotional_apr": _to_float(item.get("promotional_apr", 0.0)),
        "interest_charged": _to_float(item.get("interest_charged", 0.0)),
        "direct_debit_enabled": direct_debit_enabled,
        "payment_status": payment_status,
        "notes": _clean_text(item.get("notes")),
    }


class FinanceDataStore:
    def __init__(self, data_file: str | None = None):
        base_dir = Path(__file__).resolve().parents[1]
        self.data_file = Path(data_file) if data_file else base_dir / "data" / "finance_data.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.data_file.exists():
            self.save(DEFAULT_DATA)
            return dict(DEFAULT_DATA)

        with self.data_file.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)

        merged = dict(DEFAULT_DATA)
        for key, value in loaded.items():
            merged[key] = value

        if isinstance(loaded.get("credit_cards"), list):
            merged["credit_cards"] = [normalize_credit_card(item) for item in loaded["credit_cards"]]

        if "monthly_income" not in merged and "income" in merged:
            merged["monthly_income"] = merged["income"]
        if "monthly_expenses" not in merged and "fixed_expenses" in merged:
            merged["monthly_expenses"] = merged["fixed_expenses"]

        if "income" not in merged and "monthly_income" in merged:
            merged["income"] = merged["monthly_income"]
        if "fixed_expenses" not in merged and "monthly_expenses" in merged:
            merged["fixed_expenses"] = merged["monthly_expenses"]

        return merged

    def save(self, data):
        with self.data_file.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
