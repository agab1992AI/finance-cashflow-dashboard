import unittest

from app.finance import FinanceSummary


class FinanceSummaryTests(unittest.TestCase):
    def test_goal_totals_are_calculated_from_goals_data(self):
        data = {
            "bank_accounts": [{"name": "Main", "balance": 2500.0}],
            "savings": [{"name": "Emergency", "balance": 900.0}],
            "credit_cards": [{"name": "Card", "balance": 300.0}],
            "investments": [{"name": "Portfolio", "value": 4000.0}],
            "loans": [{"name": "Car", "balance": 500.0}],
            "goals": [
                {"name": "Driving Licence", "target_amount": 1500.0, "current_amount": 400.0},
                {"name": "Holiday", "target_amount": 2000.0, "current_amount": 1000.0},
            ],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_bank_accounts(), 2500.0)
        self.assertEqual(summary.total_savings(), 900.0)
        self.assertEqual(summary.total_credit_cards(), 300.0)
        self.assertEqual(summary.total_investments(), 4000.0)
        self.assertEqual(summary.total_loans(), 500.0)
        self.assertEqual(summary.total_goals_target(), 3500.0)
        self.assertEqual(summary.total_goals_current(), 1400.0)
        self.assertEqual(summary.total_goals_remaining(), 2100.0)

    def test_negative_bank_balance_is_treated_as_debt_not_asset(self):
        data = {
            "bank_accounts": [{
                "name": "Main",
                "balance": -1386.98,
                "overdraft_limit": 1410.0,
                "overdraft_used": 1386.98,
                "available_overdraft": 23.02,
            }],
            "savings": [{"name": "Emergency", "balance": 900.0}],
            "credit_cards": [{"name": "Card", "balance": 200.0}],
            "loans": [{"name": "Car", "balance": 500.0}],
            "investments": [{"name": "Portfolio", "value": 4000.0}],
            "monthly_income": [{"name": "Salary", "amount": 3000.0}],
            "direct_debits": [{"name": "Utility", "amount": 50.0}],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_bank_accounts(), -1386.98)
        self.assertEqual(summary.total_assets(), 4900.0)
        self.assertEqual(summary.total_cash(), 900.0)
        self.assertEqual(summary.total_debt(), 2086.98)
        self.assertEqual(summary.net_worth(), 2813.02)
        self.assertEqual(summary.total_available_overdraft(), 23.02)

    def test_positive_credit_card_balance_counts_toward_total_debt(self):
        data = {
            "credit_cards": [{"name": "Card", "current_balance": 125.50}],
            "bank_accounts": [{"name": "Main", "balance": 1000.0}],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_credit_cards(), 125.5)
        self.assertEqual(summary.total_debt(), 125.5)

    def test_zero_credit_card_balance_contributes_zero_to_total_debt(self):
        data = {
            "credit_cards": [{"name": "Card", "current_balance": 0.0}],
            "bank_accounts": [{"name": "Main", "balance": 1000.0}],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_credit_cards(), 0.0)
        self.assertEqual(summary.total_debt(), 0.0)

    def test_negative_credit_card_balance_does_not_reduce_total_debt(self):
        data = {
            "credit_cards": [{"name": "Capital One", "current_balance": -0.26, "statement_balance": -0.26}],
            "bank_accounts": [{"name": "Main", "balance": 1000.0}],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_credit_cards(), 0.0)
        self.assertEqual(summary.total_debt(), 0.0)
        self.assertEqual(data["credit_cards"][0]["current_balance"], -0.26)

    def test_total_debt_includes_loans_and_other_debts_with_expected_value(self):
        data = {
            "bank_accounts": [{
                "name": "Main",
                "balance": -8369.81,
                "overdraft_limit": 8369.81,
                "overdraft_used": 8369.81,
            }],
            "credit_cards": [{
                "name": "Capital One",
                "current_balance": 8369.81,
                "statement_balance": 8369.81,
            }],
            "loans": [{"name": "Tesco Bank", "current_balance": 11083.20}],
            "other_debts": [{"name": "HMRC", "current_balance": 1028.14}, {"name": "Currys Flexpay", "current_balance": 927.99}],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_credit_cards(), 8369.81)
        self.assertAlmostEqual(summary.total_loans(), 11083.20 + 1028.14 + 927.99)
        self.assertAlmostEqual(summary.total_debt(), 29778.95)
        self.assertEqual(summary.net_worth(), summary.total_assets() - summary.total_debt())

    def test_total_debt_uses_canonical_debt_sources_only(self):
        data = {
            "bank_accounts": [{
                "name": "Main",
                "balance": -400.0,
                "overdraft_limit": 500.0,
                "overdraft_used": 400.0,
            }],
            "credit_cards": [{
                "name": "Card",
                "current_balance": 250.0,
                "statement_balance": 1200.0,
                "credit_limit": 500.0,
            }],
            "loans": [{"name": "Car", "current_balance": 600.0}],
            "other_debts": [{"name": "Tax", "current_balance": 150.0}],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_credit_cards(), 250.0)
        self.assertEqual(summary.total_loans(), 750.0)
        self.assertEqual(summary.total_debt(), 1400.0)
        self.assertEqual(summary.net_worth(), summary.total_assets() - summary.total_debt())

    def test_total_debt_does_not_use_equality_based_overlap_deduction(self):
        data = {
            "bank_accounts": [{
                "name": "Main",
                "balance": -250.0,
                "overdraft_limit": 500.0,
                "overdraft_used": 250.0,
            }],
            "credit_cards": [{
                "name": "Card",
                "current_balance": 250.0,
                "statement_balance": 300.0,
                "credit_limit": 500.0,
            }],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_credit_cards(), 250.0)
        self.assertEqual(summary.total_debt(), 500.0)
        self.assertEqual(summary.net_worth(), summary.total_assets() - summary.total_debt())

    def test_net_worth_uses_assets_minus_total_debt_only(self):
        data = {
            "bank_accounts": [
                {"name": "Main", "balance": 3200.0},
                {"name": "Overdraft", "balance": -400.0, "overdraft_limit": 500.0, "overdraft_used": 400.0},
            ],
            "savings": [{"name": "Emergency", "balance": 750.0}],
            "investments": [{"name": "Portfolio", "value": 1500.0}],
            "credit_cards": [{"name": "Card", "current_balance": 250.0, "statement_balance": 500.0, "credit_limit": 1000.0}],
            "loans": [{"name": "Car", "current_balance": 600.0}],
            "other_debts": [{"name": "Tax", "current_balance": 150.0}],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_assets(), 3200.0 + 750.0 + 1500.0)
        self.assertEqual(summary.total_debt(), 250.0 + 600.0 + 150.0 + 400.0)
        self.assertEqual(summary.net_worth(), 5450.0 - 1400.0)
        self.assertEqual(summary.net_worth(), summary.total_assets() - summary.total_debt())

    def test_liabilities_are_not_counted_as_assets_or_double_counted(self):
        data = {
            "bank_accounts": [{"name": "Main", "balance": 1000.0}],
            "credit_cards": [{"name": "Card", "current_balance": 200.0}],
            "loans": [{"name": "Car", "current_balance": 900.0}],
            "other_debts": [{"name": "Tax", "current_balance": 50.0}],
        }

        summary = FinanceSummary(data)

        self.assertEqual(summary.total_assets(), 1000.0)
        self.assertEqual(summary.total_debt(), 1150.0)
        self.assertEqual(summary.net_worth(), -150.0)
        self.assertNotIn(200.0, [summary.total_assets(), summary.total_debt()])
        self.assertNotIn(900.0, [summary.total_assets(), summary.total_debt()])


if __name__ == "__main__":
    unittest.main()
