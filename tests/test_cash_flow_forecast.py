import unittest
from datetime import date

from app.forecast import ForecastValidationError, calculate_cash_flow_forecast


class CashFlowForecastTests(unittest.TestCase):
    def test_multiple_payment_dates_and_running_balance(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1),
            date(2026, 11, 20),
            1000,
            [
                {"id": "salary", "date": date(2026, 11, 5), "amount": 1500, "type": "income", "status": "confirmed"},
                {"id": "rent", "date": date(2026, 11, 6), "amount": -1200, "type": "bill", "status": "unpaid"},
                {"id": "card", "date": date(2026, 11, 10), "amount": -100, "type": "card_minimum", "status": "unpaid"},
            ],
        )

        balances = {row["date"]: row["balance"] for row in result["running_balances"]}
        self.assertEqual(balances[date(2026, 11, 5)], 2500.0)
        self.assertEqual(balances[date(2026, 11, 6)], 1300.0)
        self.assertEqual(balances[date(2026, 11, 10)], 1200.0)

    def test_earliest_shortfall_is_reported(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 30), 500,
            [
                {"id": "rent", "date": "2026-11-03", "amount": "-600", "type": "bill", "status": "unpaid"},
                {"id": "later", "date": "2026-11-12", "amount": "-100", "type": "expense", "status": "unpaid"},
            ],
        )
        self.assertEqual(result["earliest_shortfall"], date(2026, 11, 3))

    def test_same_day_events_are_deterministic(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 2), 100,
            [
                {"id": "outflow", "date": "2026-11-02", "amount": -150, "type": "bill", "status": "unpaid"},
                {"id": "income", "date": "2026-11-02", "amount": 100, "type": "income", "status": "confirmed"},
            ],
        )
        day = result["running_balances"][-1]
        self.assertEqual(day["balance"], 50.0)

    def test_duplicate_event_identifier_is_rejected(self):
        with self.assertRaisesRegex(ForecastValidationError, "Duplicate event identifier"):
            calculate_cash_flow_forecast(
                date(2026, 11, 1), date(2026, 11, 2), 100,
                [
                    {"id": "rent", "date": "2026-11-02", "amount": -50, "type": "bill", "status": "unpaid"},
                    {"id": "rent", "date": "2026-11-02", "amount": -75, "type": "bill", "status": "unpaid"},
                ],
            )

    def test_missing_event_date_is_rejected(self):
        with self.assertRaisesRegex(ForecastValidationError, "Missing or invalid date"):
            calculate_cash_flow_forecast(
                date(2026, 11, 1), date(2026, 11, 2), 100,
                [{"id": "rent", "amount": -50, "type": "bill", "status": "unpaid"}],
            )

    def test_invalid_date_format_is_rejected(self):
        with self.assertRaisesRegex(ForecastValidationError, "Invalid date"):
            calculate_cash_flow_forecast(
                date(2026, 11, 1), date(2026, 11, 2), 100,
                [{"id": "rent", "date": "tomorrow", "amount": -50, "type": "bill", "status": "unpaid"}],
            )

    def test_historical_and_already_paid_events_are_not_forecast(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 5), 300,
            [
                {"id": "paid-rent", "date": "2026-10-30", "amount": -200, "type": "bill", "status": "paid"},
                {"id": "paid-card", "date": "2026-11-02", "amount": -50, "type": "card_minimum", "status": "fully paid"},
            ],
        )
        self.assertIsNone(result["earliest_shortfall"])
        self.assertEqual(result["running_balances"][-1]["balance"], 300.0)

    def test_no_savings_by_default(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 2), 300, [],
        )
        self.assertEqual(result["savings_transferred"], 0.0)
        self.assertEqual(result["remaining_savings"], 0.0)

    def test_partial_savings_transfer_and_remaining_savings(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 5), 100,
            [{"id": "rent", "date": "2026-11-3", "amount": -150, "type": "bill", "status": "unpaid"}],
            savings_contribution=75,
            available_savings_balance=200,
            savings_transfer_date="2026-11-2",
        )
        balances = {row["date"]: row["balance"] for row in result["running_balances"]}
        self.assertEqual(balances[date(2026, 11, 2)], 175.0)
        self.assertEqual(balances[date(2026, 11, 3)], 25.0)
        self.assertEqual(result["remaining_savings"], 125.0)

    def test_full_savings_transfer(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 2), 20, [],
            savings_contribution=100,
            available_savings_balance=100,
            savings_transfer_date="2026-11-1",
        )
        self.assertEqual(result["remaining_savings"], 0.0)
        self.assertEqual(result["savings_transferred"], 100.0)

    def test_invalid_savings_amount_or_balance_is_rejected(self):
        for contribution, balance in ((-1, 100), (101, 100), ("bad", 100), (10, -1)):
            with self.subTest(contribution=contribution, balance=balance):
                with self.assertRaises(ForecastValidationError):
                    calculate_cash_flow_forecast(
                        date(2026, 11, 1), date(2026, 11, 2), 100, [],
                        savings_contribution=contribution,
                        available_savings_balance=balance,
                        savings_transfer_date="2026-11-1",
                    )

    def test_missing_savings_transfer_date_is_rejected(self):
        with self.assertRaisesRegex(ForecastValidationError, "Savings transfer date"):
            calculate_cash_flow_forecast(
                date(2026, 11, 1), date(2026, 11, 2), 100, [],
                savings_contribution=50,
                available_savings_balance=100,
            )

    def test_internal_transfer_is_not_allowed_as_a_cashflow_event(self):
        with self.assertRaisesRegex(ForecastValidationError, "Internal transfer event"):
            calculate_cash_flow_forecast(
                date(2026, 11, 1), date(2026, 11, 2), 100,
                [{"id": "move", "date": "2026-11-2", "amount": -50, "type": "internal_transfer", "status": "unpaid"}],
                available_savings_balance=100,
            )

    def test_invalid_amount_is_rejected(self):
        with self.assertRaisesRegex(ForecastValidationError, "Invalid amount"):
            calculate_cash_flow_forecast(
                date(2026, 11, 1), date(2026, 11, 2), 100,
                [{"id": "bad", "date": "2026-11-2", "amount": "not-money", "type": "bill", "status": "unpaid"}],
            )


if __name__ == "__main__":
    unittest.main()
