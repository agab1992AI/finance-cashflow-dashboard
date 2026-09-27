import unittest
from datetime import date

from app.pay_cycle import CurrentPayCycle, build_current_pay_cycle


class CurrentPayCycleTests(unittest.TestCase):
    def test_cycle_uses_latest_salary_as_current_payday_and_filters_transactions(self):
        data = {
            "monthly_income": [
                {"source": "Salary", "amount": 3000.0, "date": "2026-09-15", "received_status": "received"},
                {"source": "Salary", "amount": 3000.0, "date": "2026-10-15", "received_status": "received"},
            ],
            "monthly_expenses": [
                {"name": "Rent", "amount": 1200.0, "due_date": "2026-09-18", "status": "not paid", "classification": "expense"},
                {"name": "Old rent", "amount": 1200.0, "due_date": "2026-10-20", "status": "not paid", "classification": "expense"},
            ],
            "direct_debits": [
                {"name": "Internet", "amount": 52.0, "due_date": "2026-09-20", "status": "paid", "classification": "expense"},
            ],
            "payments_completed": [
                {"name": "Cashback", "amount": 15.0, "date": "2026-09-19", "classification": "cashback_reward"},
            ],
        }

        cycle = build_current_pay_cycle(data, as_of=date(2026, 9, 20))

        self.assertEqual(cycle.payday_date, date(2026, 9, 15))
        self.assertEqual(cycle.cycle_start, date(2026, 9, 15))
        self.assertEqual(cycle.cycle_end, date(2026, 10, 15))
        self.assertEqual(cycle.total_income(), 3000.0)
        self.assertEqual(cycle.total_expenses(), 1200.0)
        self.assertEqual(cycle.net_cashflow(), 1800.0)
        self.assertEqual(len(cycle.income_entries), 1)
        self.assertEqual(len(cycle.expense_entries), 1)

    def test_cycle_reuses_milestone_3_classification_rules_and_excludes_non_cashflow_entries(self):
        data = {
            "monthly_income": [
                {"source": "Salary", "amount": 2800.0, "date": "2026-09-15", "classification": "income"},
            ],
            "monthly_expenses": [
                {"name": "Rent", "amount": 1000.0, "due_date": "2026-09-17", "classification": "expense"},
                {"name": "Household transfer", "amount": 80.0, "due_date": "2026-09-17", "classification": "transfer"},
                {"name": "Investment contribution", "amount": 200.0, "due_date": "2026-09-17", "classification": "investment_contribution"},
            ],
            "payments_completed": [
                {"name": "Cashback reward", "amount": 25.0, "date": "2026-09-16", "classification": "cashback_reward"},
            ],
        }

        cycle = build_current_pay_cycle(data, as_of=date(2026, 9, 20))

        self.assertEqual(cycle.total_income(), 2800.0)
        self.assertEqual(cycle.total_expenses(), 1000.0)
        self.assertEqual(cycle.net_cashflow(), 1800.0)
        self.assertEqual(len(cycle.classified_income_entries), 1)
        self.assertEqual(len(cycle.classified_expense_entries), 1)

    def test_cycle_ignores_outside_cycle_and_missing_dates(self):
        data = {
            "monthly_income": [
                {"source": "Salary", "amount": 2500.0, "date": "2026-08-15", "received_status": "received"},
                {"source": "Salary", "amount": 2500.0, "date": "2026-09-15", "received_status": "received"},
            ],
            "monthly_expenses": [
                {"name": "Rent", "amount": 900.0, "due_date": "2026-09-18", "status": "not paid", "classification": "expense"},
                {"name": "Late bill", "amount": 250.0, "due_date": "2026-08-10", "status": "not paid", "classification": "expense"},
                {"name": "Broken date", "amount": 10.0, "due_date": "unknown", "status": "not paid", "classification": "expense"},
            ],
        }

        cycle = build_current_pay_cycle(data, as_of=date(2026, 9, 20))

        self.assertEqual(cycle.payday_date, date(2026, 9, 15))
        self.assertEqual(cycle.cycle_start, date(2026, 9, 15))
        self.assertEqual(cycle.cycle_end, None)
        self.assertEqual(cycle.total_expenses(), 900.0)
        self.assertEqual(cycle.income_entries[0]["date"], "2026-09-15")

    def test_cycle_handles_legacy_records_and_obligations_without_crashing(self):
        data = {
            "income": [
                {"source": "Salary", "amount": 3200.0, "date": "2026-09-15"},
            ],
            "fixed_expenses": [
                {"name": "Rent", "amount": 1100.0, "due_date": "2026-09-18", "status": "not paid"},
            ],
            "payments_pending": [
                {"name": "Returned card", "amount": 40.0, "status": "returned"},
            ],
            "credit_cards": [
                {
                    "card_name": "Vanquis",
                    "current_balance": 250.0,
                    "statement_balance": 250.0,
                    "payment_due_date": "2026-09-30",
                    "minimum_payment_due": 25.0,
                    "amount_paid_this_statement": 0.0,
                    "payment_status": "Unpaid / upcoming",
                    "classification": "expense",
                }
            ],
        }

        cycle = build_current_pay_cycle(data, as_of=date(2026, 9, 20))

        self.assertEqual(cycle.payday_date, date(2026, 9, 15))
        self.assertEqual(cycle.total_income(), 3200.0)
        self.assertEqual(cycle.total_expenses(), 1100.0)
        self.assertEqual(cycle.net_cashflow(), 2100.0)
        self.assertGreaterEqual(len(cycle.obligations), 1)


if __name__ == "__main__":
    unittest.main()
