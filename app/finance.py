from app.data_store import infer_default_transaction_type_for_collection, normalize_transaction_type


class FinanceSummary:
    """Financial summary model for the CashFlow AI dashboard."""

    def __init__(self, data):
        self.data = data

    def _sum_items(self, key, value_key):
        total = 0.0
        for item in self.data.get(key, []):
            try:
                total += float(item.get(value_key, 0.0))
            except (TypeError, ValueError):
                continue
        return total

    def _sum_classified_items(self, key, value_key, allowed_types, default_type=None):
        total = 0.0
        for item in self.data.get(key, []):
            if not isinstance(item, dict):
                continue
            classification = normalize_transaction_type(
                item.get("classification") or item.get("type") or item.get("transaction_type"),
                default=default_type or infer_default_transaction_type_for_collection(key),
            )
            if classification not in allowed_types:
                continue
            try:
                total += float(item.get(value_key, 0.0))
            except (TypeError, ValueError):
                continue
        return total

    def _sum_positive_bank_balances(self):
        total = 0.0
        for item in self.data.get("bank_accounts", []):
            try:
                balance = float(item.get("balance", 0.0))
            except (TypeError, ValueError):
                continue
            if balance > 0:
                total += balance
        return total

    def _sum_negative_overdraft_debt(self):
        total = 0.0
        for item in self.data.get("bank_accounts", []):
            try:
                balance = float(item.get("balance", 0.0))
                overdraft_used = float(item.get("overdraft_used", 0.0))
            except (TypeError, ValueError):
                continue

            if balance < 0:
                total += overdraft_used if overdraft_used > 0 else abs(balance)
        return total

    def _duplicate_overdraft_overlap(self):
        return 0.0

    def _effective_overdraft_debt(self):
        return self._sum_negative_overdraft_debt()

    def _sum_overdraft_available(self):
        total = 0.0
        for item in self.data.get("bank_accounts", []):
            try:
                overdraft_limit = float(item.get("overdraft_limit", 0.0))
                overdraft_used = float(item.get("overdraft_used", 0.0))
            except (TypeError, ValueError):
                continue

            if overdraft_limit > 0 and overdraft_used >= 0:
                available = overdraft_limit - overdraft_used
                if available > 0:
                    total += available
        return total

    def total_bank_accounts(self):
        return self._sum_items("bank_accounts", "balance")

    def total_cash(self):
        return self._sum_positive_bank_balances() + self.total_savings()

    def total_savings(self):
        return self._sum_items("savings", "balance")

    def _sum_positive_debt_value_fields(self, key, *value_keys):
        total = 0.0
        for item in self.data.get(key, []):
            for value_key in value_keys:
                try:
                    value = float(item.get(value_key, 0.0))
                except (TypeError, ValueError):
                    continue
                if value > 0:
                    total += value
                    break
        return total

    def total_credit_cards(self):
        return self._sum_positive_debt_value_fields("credit_cards", "current_balance", "balance")

    def total_loans(self):
        return (
            self._sum_positive_debt_value_fields("loans", "current_balance", "balance")
            + self._sum_positive_debt_value_fields("other_debts", "current_balance", "balance")
        )

    def total_investments(self):
        return self._sum_items("investments", "value") + self._sum_items("trading_212", "value")

    def total_assets(self):
        return self.total_cash() + self.total_investments()

    def total_debt(self):
        return self.total_credit_cards() + self.total_loans() + self._effective_overdraft_debt()

    def total_available_cash(self):
        return self.total_cash()

    def total_available_overdraft(self):
        return round(self._sum_overdraft_available(), 2)

    def net_worth(self):
        return self.total_assets() - self.total_debt()

    def total_income(self):
        return (
            self._sum_classified_items("monthly_income", "amount", {"income"}, default_type="income")
            + self._sum_classified_items("income", "amount", {"income"}, default_type="income")
        )

    def total_fixed_expenses(self):
        return (
            self._sum_classified_items("monthly_expenses", "amount", {"expense"}, default_type="expense")
            + self._sum_classified_items("fixed_expenses", "amount", {"expense"}, default_type="expense")
        )

    def total_goals_target(self):
        return self._sum_items("goals", "target_amount")

    def total_goals_current(self):
        return self._sum_items("goals", "current_amount")

    def total_goals_remaining(self):
        return max(self.total_goals_target() - self.total_goals_current(), 0.0)

    def total_goals_progress(self):
        target = self.total_goals_target()
        if target <= 0:
            return 0.0
        return min((self.total_goals_current() / target) * 100.0, 100.0)

    def upcoming_critical_payments(self):
        return self._sum_items("direct_debits", "amount") + self._sum_items("payments_pending", "amount")

    def safe_to_spend_until_payday(self):
        return max(self.total_cash() - self.upcoming_critical_payments(), 0.0)

    def financial_status(self):
        available = self.total_cash()
        debt = self.total_debt()
        critical = self.upcoming_critical_payments()
        income = self.total_income()

        if debt > income * 0.65 or available < critical:
            return "Red"
        if available < income * 0.35:
            return "Amber"
        return "Green"
