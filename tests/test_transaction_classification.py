import unittest

from app.data_store import CANONICAL_TRANSACTION_TYPES, normalize_transaction_type
from app.finance import FinanceSummary


class TransactionClassificationTests(unittest.TestCase):
    def test_every_canonical_type_is_supported(self):
        for canonical in CANONICAL_TRANSACTION_TYPES:
            self.assertEqual(normalize_transaction_type(canonical), canonical)

    def test_legacy_values_map_to_canonical_types(self):
        self.assertEqual(normalize_transaction_type("earned_income"), "income")
        self.assertEqual(normalize_transaction_type("salary"), "income")
        self.assertEqual(normalize_transaction_type("expense"), "expense")
        self.assertEqual(normalize_transaction_type("essential_living"), "expense")
        self.assertEqual(normalize_transaction_type("internal_transfer"), "transfer")
        self.assertEqual(normalize_transaction_type("transfer"), "transfer")
        self.assertEqual(normalize_transaction_type("household_reimbursement"), "reimbursement")
        self.assertEqual(normalize_transaction_type("reimbursement"), "reimbursement")
        self.assertEqual(normalize_transaction_type("dividend"), "investment_income")
        self.assertEqual(normalize_transaction_type("dividends"), "investment_income")
        self.assertEqual(normalize_transaction_type("cashback"), "cashback_reward")
        self.assertEqual(normalize_transaction_type("reward"), "cashback_reward")
        self.assertEqual(normalize_transaction_type("investment_contribution"), "investment_contribution")
        self.assertEqual(normalize_transaction_type("auto_invest"), "investment_contribution")

    def test_transfers_and_reimbursements_are_excluded_from_ordinary_cashflow_totals(self):
        data = {
            "monthly_income": [
                {"source": "Salary", "amount": 3000.0, "classification": "income"},
                {"source": "Partner share", "amount": 400.0, "classification": "reimbursement"},
                {"source": "Move between own accounts", "amount": 250.0, "classification": "transfer"},
            ],
            "monthly_expenses": [
                {"name": "Rent", "amount": 1200.0, "classification": "expense"},
                {"name": "Household transfer", "amount": 75.0, "classification": "transfer"},
                {"name": "Reimbursable cost", "amount": 50.0, "classification": "reimbursement"},
            ],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_income(), 3000.0)
        self.assertEqual(summary.total_fixed_expenses(), 1200.0)

    def test_dividends_and_cashback_are_not_treated_as_ordinary_income(self):
        data = {
            "monthly_income": [
                {"source": "Salary", "amount": 2500.0, "classification": "income"},
                {"source": "Dividend", "amount": 120.0, "classification": "investment_income"},
                {"source": "Cashback reward", "amount": 15.0, "classification": "cashback_reward"},
            ],
            "monthly_expenses": [
                {"name": "Essential living", "amount": 900.0, "classification": "expense"},
            ],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_income(), 2500.0)
        self.assertEqual(summary.total_fixed_expenses(), 900.0)

    def test_investment_contribution_is_not_treated_as_regular_expense(self):
        data = {
            "monthly_expenses": [
                {"name": "Rent", "amount": 1200.0, "classification": "expense"},
                {"name": "Auto invest reward", "amount": 45.0, "classification": "investment_contribution"},
            ],
            "monthly_income": [
                {"source": "Salary", "amount": 3100.0, "classification": "income"},
            ],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_income(), 3100.0)
        self.assertEqual(summary.total_fixed_expenses(), 1200.0)

    def test_legacy_records_still_load_with_default_mapping(self):
        legacy_data = {
            "monthly_income": [{"source": "Salary", "amount": 2000.0}],
            "monthly_expenses": [{"name": "Rent", "amount": 900.0}],
            "payments_completed": [{"name": "Cashback", "amount": 25.0, "classification": "cashback_reward"}],
        }

        summary = FinanceSummary(legacy_data)

        self.assertEqual(summary.total_income(), 2000.0)
        self.assertEqual(summary.total_fixed_expenses(), 900.0)

    def test_cashback_auto_investment_cannot_be_double_counted(self):
        data = {
            "monthly_income": [
                {"source": "Salary", "amount": 3500.0, "classification": "income"},
            ],
            "monthly_expenses": [
                {"name": "Living", "amount": 1600.0, "classification": "expense"},
                {"name": "Auto invest cashback", "amount": 20.0, "classification": "investment_contribution"},
                {"name": "Cashback reward paid out", "amount": 20.0, "classification": "cashback_reward"},
            ],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_income(), 3500.0)
        self.assertEqual(summary.total_fixed_expenses(), 1600.0)


if __name__ == "__main__":
    unittest.main()
