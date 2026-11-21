import unittest
from datetime import date
from decimal import Decimal

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
        self.assertEqual(balances[date(2026, 11, 5)], Decimal("2500.00"))
        self.assertEqual(balances[date(2026, 11, 6)], Decimal("1300.00"))
        self.assertEqual(balances[date(2026, 11, 10)], Decimal("1200.00"))

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
        self.assertEqual(day["balance"], Decimal("50.00"))

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
        self.assertEqual(result["running_balances"][-1]["balance"], Decimal("300.00"))

    def test_no_savings_by_default(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 2), 300, [],
        )
        self.assertEqual(result["savings_transferred"], Decimal("0.00"))
        self.assertEqual(result["remaining_savings"], Decimal("0.00"))

    def test_partial_savings_transfer_and_remaining_savings(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 5), 100,
            [{"id": "rent", "date": "2026-11-3", "amount": -150, "type": "bill", "status": "unpaid"}],
            savings_contribution=75,
            available_savings_balance=200,
            savings_transfer_date="2026-11-2",
        )
        balances = {row["date"]: row["balance"] for row in result["running_balances"]}
        self.assertEqual(balances[date(2026, 11, 2)], Decimal("175.00"))
        self.assertEqual(balances[date(2026, 11, 3)], Decimal("25.00"))
        self.assertEqual(result["remaining_savings"], Decimal("125.00"))

    def test_full_savings_transfer(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 2), 20, [],
            savings_contribution=100,
            available_savings_balance=100,
            savings_transfer_date="2026-11-1",
        )
        self.assertEqual(result["remaining_savings"], Decimal("0.00"))
        self.assertEqual(result["savings_transferred"], Decimal("100.00"))

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

    def test_missing_outflow_status_is_rejected(self):
        for status in (None, "", "   "):
            event = {"id": "rent", "date": "2026-11-02", "amount": -50, "type": "bill"}
            if status is not None:
                event["status"] = status
            with self.subTest(status=status):
                with self.assertRaisesRegex(ForecastValidationError, "explicit status"):
                    calculate_cash_flow_forecast(
                        date(2026, 11, 1), date(2026, 11, 2), 100, [event]
                    )

    def test_negative_opening_cash_has_initial_shortfall(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 3), Decimal("-25.50"),
            [{"id": "income", "date": "2026-11-02", "amount": 10, "type": "income", "status": "confirmed"}],
        )
        self.assertEqual(result["earliest_shortfall"], date(2026, 11, 1))
        balances = {row["date"]: row["balance"] for row in result["running_balances"]}
        self.assertEqual(balances[date(2026, 11, 1)], Decimal("-25.50"))
        self.assertEqual(balances[date(2026, 11, 2)], Decimal("-15.50"))

    def test_fractional_penny_values_are_rejected_everywhere(self):
        cases = (
            ("starting", {"starting_spendable_cash": "100.001"}),
            ("event", {"events": [{"id": "rent", "date": "2026-11-02", "amount": "-50.001", "type": "bill", "status": "unpaid"}]}),
            ("contribution", {"savings_contribution": "10.001", "available_savings_balance": "100.00", "savings_transfer_date": "2026-11-02"}),
            ("savings", {"available_savings_balance": "100.001"}),
        )
        for name, kwargs in cases:
            with self.subTest(name=name):
                arguments = dict(
                    forecast_start=date(2026, 11, 1),
                    forecast_end=date(2026, 11, 2),
                    starting_spendable_cash=100,
                    events=[],
                )
                if name == "starting":
                    arguments["starting_spendable_cash"] = kwargs["starting_spendable_cash"]
                elif name == "event":
                    arguments["events"] = kwargs["events"]
                else:
                    arguments.update(kwargs)
                with self.assertRaisesRegex(ForecastValidationError, "fractional pennies"):
                    calculate_cash_flow_forecast(**arguments)

    def test_same_day_forecast_start_and_end_boundaries(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 2), date(2026, 11, 2), Decimal("100.00"),
            [
                {"id": "start-income", "date": date(2026, 11, 2), "amount": Decimal("25.00"), "type": "income", "status": "scheduled"},
                {"id": "start-bill", "date": date(2026, 11, 2), "amount": Decimal("-40.00"), "type": "bill", "status": "overdue"},
            ],
        )
        self.assertEqual(result["running_balances"], [{"date": date(2026, 11, 2), "balance": Decimal("85.00")}])
        self.assertIsNone(result["earliest_shortfall"])

    def test_events_exactly_on_start_and_end_dates_are_included(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 3), Decimal("50.00"),
            [
                {"id": "at-start", "date": "2026-11-01", "amount": 10, "type": "income", "status": "confirmed"},
                {"id": "at-end", "date": "2026-11-03", "amount": -20, "type": "bill", "status": "pending"},
            ],
        )
        balances = {row["date"]: row["balance"] for row in result["running_balances"]}
        self.assertEqual(balances[date(2026, 11, 1)], Decimal("60.00"))
        self.assertEqual(balances[date(2026, 11, 3)], Decimal("40.00"))

    def test_savings_and_outgoing_payment_on_same_day_are_not_double_counted(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 2), Decimal("100.00"),
            [{"id": "rent", "date": "2026-11-02", "amount": Decimal("-40.00"), "type": "bill", "status": "unpaid"}],
            savings_contribution=Decimal("30.00"),
            available_savings_balance=Decimal("30.00"),
            savings_transfer_date="2026-11-02",
        )
        self.assertEqual(result["running_balances"][-1]["balance"], Decimal("90.00"))
        self.assertEqual(result["savings_transferred"], Decimal("30.00"))
        self.assertEqual(result["remaining_savings"], Decimal("0.00"))
        savings_events = [event for event in result["events"] if event[3] == "savings_transfer"]
        self.assertEqual(len(savings_events), 1)
        self.assertEqual(savings_events[0][4], Decimal("30.00"))

    def test_duplicate_ids_with_leading_or_trailing_whitespace_are_rejected(self):
        with self.assertRaisesRegex(ForecastValidationError, "Duplicate event identifier"):
            calculate_cash_flow_forecast(
                date(2026, 11, 1), date(2026, 11, 2), 100,
                [
                    {"id": " rent ", "date": "2026-11-01", "amount": -10, "type": "bill", "status": "unpaid"},
                    {"id": "rent", "date": "2026-11-02", "amount": -10, "type": "bill", "status": "unpaid"},
                ],
            )

    def test_duplicate_savings_transfer_id_is_rejected(self):
        with self.assertRaisesRegex(ForecastValidationError, "Duplicate event identifier: __savings_transfer__"):
            calculate_cash_flow_forecast(
                date(2026, 11, 1), date(2026, 11, 2), 100,
                [{"id": "__savings_transfer__", "date": "2026-11-01", "amount": -10, "type": "bill", "status": "paid"}],
                savings_contribution=10,
                available_savings_balance=100,
                savings_transfer_date="2026-11-02",
            )

    def test_missing_dates_or_amounts_on_paid_events_are_safely_excluded(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 2), Decimal("100.00"),
            [
                {"id": "paid-missing-date", "amount": -50, "type": "bill", "status": "paid"},
                {"id": "paid-missing-amount", "date": "2026-11-02", "type": "bill", "status": "completed"},
                {"id": "paid-internal-transfer", "amount": -20, "type": "internal_transfer", "status": "cleared"},
            ],
        )
        self.assertEqual(result["earliest_shortfall"], None)
        self.assertEqual(result["running_balances"][-1]["balance"], Decimal("100.00"))

    def test_unusually_long_forecast_range_is_processed_exactly(self):
        start = date(2024, 1, 1)
        end = date(2034, 12, 31)
        result = calculate_cash_flow_forecast(start, end, Decimal("1.00"), [])
        self.assertEqual(len(result["running_balances"]), 4018)
        self.assertEqual(result["running_balances"][0]["balance"], Decimal("1.00"))
        self.assertEqual(result["running_balances"][-1]["balance"], Decimal("1.00"))

    def test_paid_internal_transfer_is_excluded_not_rejected(self):
        result = calculate_cash_flow_forecast(
            date(2026, 11, 1), date(2026, 11, 2), Decimal("100.00"),
            [{"id": "paid-transfer", "date": "2026-11-02", "amount": -50, "type": "internal_transfer", "status": "paid"}],
        )
        self.assertEqual(result["running_balances"][-1]["balance"], Decimal("100.00"))

    def test_minimum_paid_card_event_is_excluded_from_cash_outflows(self):
        for status in ("Minimum paid", "minimum paid", "PAID", "Fully paid", "Completed"):
            with self.subTest(status=status):
                result = calculate_cash_flow_forecast(
                    date(2026, 11, 1),
                    date(2026, 11, 5),
                    Decimal("300.00"),
                    [{
                        "id": f"card-{status.lower().replace(' ', '-')}",
                        "date": "2026-11-03",
                        "amount": Decimal("-50.00"),
                        "type": "card_minimum",
                        "status": status,
                    }],
                )
                self.assertIsNone(result["earliest_shortfall"])
                self.assertEqual(result["running_balances"][-1]["balance"], Decimal("300.00"))


if __name__ == "__main__":
    unittest.main()
