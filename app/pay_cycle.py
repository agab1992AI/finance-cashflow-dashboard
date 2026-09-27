import datetime
from typing import Any, Dict, Optional

from app.data_store import normalize_transaction_type


def _parse_date(value: Any):
    if value in (None, "", "Unknown", "N/A", "unknown"):
        return None
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, datetime.datetime):
        return value.date()

    text = str(value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _coerce_decimal(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class CurrentPayCycle:
    def __init__(self, payday_date: Optional[datetime.date], cycle_start: Optional[datetime.date], cycle_end: Optional[datetime.date], data: Dict[str, Any]):
        self.payday_date = payday_date
        self.cycle_start = cycle_start
        self.cycle_end = cycle_end
        self.data = data or {}
        self.income_entries = self._filter_entries(self._iter_income_entries())
        self.expense_entries = self._filter_entries(self._iter_expense_entries())
        self.classified_income_entries = [
            entry for entry in self.income_entries
            if normalize_transaction_type(
                entry.get("classification") or entry.get("type") or entry.get("transaction_type"),
                default="income",
            ) == "income"
        ]
        self.classified_expense_entries = [
            entry for entry in self.expense_entries
            if normalize_transaction_type(
                entry.get("classification") or entry.get("type") or entry.get("transaction_type"),
                default="expense",
            ) == "expense"
        ]
        self.obligations = self._build_obligations()

    def _iter_income_entries(self):
        for key in ("monthly_income", "income"):
            for entry in self.data.get(key, []):
                if isinstance(entry, dict):
                    yield entry

    def _iter_expense_entries(self):
        for key in ("monthly_expenses", "fixed_expenses", "direct_debits"):
            for entry in self.data.get(key, []):
                if isinstance(entry, dict):
                    yield entry

    def _filter_entries(self, entries):
        results = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status") or "").strip().lower()
            if status in {"paid", "completed", "cleared", "received"}:
                continue
            date_value = _parse_date(entry.get("date") or entry.get("due_date") or entry.get("payment_date"))
            if date_value is None:
                continue
            if self.cycle_start is not None and date_value < self.cycle_start:
                continue
            if self.cycle_end is not None and date_value >= self.cycle_end:
                continue
            results.append(entry)
        return results

    def _build_obligations(self):
        obligations = []

        for key in ("monthly_expenses", "fixed_expenses", "direct_debits"):
            for entry in self.data.get(key, []):
                if not isinstance(entry, dict):
                    continue
                status = str(entry.get("status") or "").strip().lower()
                if status not in {"not paid", "pending", "returned", "overdue"}:
                    continue
                due_date = _parse_date(entry.get("due_date") or entry.get("payment_due_date"))
                if due_date is None:
                    continue
                if self.cycle_start is not None and due_date < self.cycle_start:
                    continue
                if self.cycle_end is not None and due_date >= self.cycle_end:
                    continue
                obligations.append({
                    "name": entry.get("name") or entry.get("source") or "Expense",
                    "amount": entry.get("amount", 0.0),
                    "status": entry.get("status"),
                    "due_date": due_date.isoformat(),
                })

        for card in self.data.get("credit_cards", []):
            if not isinstance(card, dict):
                continue
            payment_status = str(card.get("payment_status") or "").strip()
            if not payment_status:
                continue
            due_date = _parse_date(card.get("payment_due_date") or card.get("statement_date"))
            if due_date is None:
                continue
            if self.cycle_start is not None and due_date < self.cycle_start:
                continue
            if self.cycle_end is not None and due_date >= self.cycle_end:
                continue
            if "paid" not in payment_status.lower():
                obligations.append({
                    "name": card.get("card_name") or "Credit card",
                    "amount": card.get("minimum_payment_due") or card.get("remaining_statement_balance") or card.get("current_balance") or 0.0,
                    "status": payment_status,
                    "due_date": due_date.isoformat(),
                })
        return obligations

    def total_income(self):
        total = 0.0
        for entry in self.classified_income_entries:
            total += _coerce_decimal(entry.get("amount"))
        return round(total, 2)

    def total_expenses(self):
        total = 0.0
        for entry in self.classified_expense_entries:
            total += _coerce_decimal(entry.get("amount"))
        return round(total, 2)

    def net_cashflow(self):
        return round(self.total_income() - self.total_expenses(), 2)


def _find_latest_payday(data, as_of):
    candidate_dates = []
    for key in ("monthly_income", "income"):
        for entry in data.get(key, []):
            if not isinstance(entry, dict):
                continue
            if normalize_transaction_type(entry.get("classification") or entry.get("type") or entry.get("transaction_type"), default="income") != "income":
                continue
            payday = _parse_date(entry.get("date") or entry.get("received_date"))
            if payday is not None and payday <= as_of:
                candidate_dates.append(payday)
    return max(candidate_dates) if candidate_dates else None


def _find_next_payday(data, payday_date):
    if payday_date is None:
        return None
    candidate_dates = []
    for key in ("monthly_income", "income"):
        for entry in data.get(key, []):
            if not isinstance(entry, dict):
                continue
            if normalize_transaction_type(entry.get("classification") or entry.get("type") or entry.get("transaction_type"), default="income") != "income":
                continue
            payday = _parse_date(entry.get("date") or entry.get("received_date"))
            if payday is not None and payday > payday_date:
                candidate_dates.append(payday)
    return min(candidate_dates) if candidate_dates else None


def build_current_pay_cycle(data: Dict[str, Any], as_of: Optional[datetime.date] = None) -> CurrentPayCycle:
    if as_of is None:
        as_of = datetime.date.today()

    payday_date = _find_latest_payday(data, as_of)
    if payday_date is None:
        payday_date = as_of

    cycle_start = payday_date
    cycle_end = _find_next_payday(data, payday_date)
    return CurrentPayCycle(payday_date, cycle_start, cycle_end, data)
