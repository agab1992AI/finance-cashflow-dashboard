import datetime

from app.obligations import build_obligations, sort_obligations


class TestPaymentPriorityEngine:
    def test_overdue_unpaid_ranks_before_upcoming_unpaid(self):
        data = {
            "credit_cards": [
                {
                    "card_name": "Overdue Card",
                    "current_balance": 500.0,
                    "credit_limit": 2000.0,
                    "minimum_payment_due": 50.0,
                    "amount_paid_this_statement": 10.0,
                    "payment_due_date": "2026-08-01",
                    "payment_status": "Overdue",
                }
            ],
            "monthly_expenses": [
                {
                    "name": "Internet",
                    "amount": 60.0,
                    "due_date": "2026-09-25",
                    "status": "not paid",
                    "critical_payment": "No",
                }
            ],
            "loans": [],
            "payments_pending": [],
        }

        result = build_obligations(data, as_of=datetime.date(2026, 9, 4))
        ranked = sort_obligations(result)

        assert ranked[0]["Account"] == "Overdue Card"
        assert ranked[0]["Priority"] == "CRITICAL"
        assert ranked[1]["Account"] == "Internet"

    def test_critical_unpaid_ranks_before_ordinary_upcoming_unpaid(self):
        data = {
            "monthly_expenses": [
                {
                    "name": "Rent",
                    "amount": 1200.0,
                    "due_date": "2026-09-20",
                    "status": "not paid",
                    "critical_payment": "Yes",
                },
                {
                    "name": "Streaming",
                    "amount": 15.0,
                    "due_date": "2026-09-28",
                    "status": "not paid",
                    "critical_payment": "No",
                },
            ],
        }

        result = sort_obligations(build_obligations(data, as_of=datetime.date(2026, 9, 4)))

        assert result[0]["Account"] == "Rent"
        assert result[0]["Priority"] == "CRITICAL"
        assert result[1]["Account"] == "Streaming"
        assert result[1]["Priority"] == "HIGH"

    def test_paid_obligation_always_ranks_after_unpaid(self):
        data = {
            "monthly_expenses": [
                {
                    "name": "Paid bill",
                    "amount": 80.0,
                    "due_date": "2026-09-10",
                    "status": "paid",
                    "critical_payment": "No",
                },
                {
                    "name": "Open bill",
                    "amount": 80.0,
                    "due_date": "2026-09-18",
                    "status": "not paid",
                    "critical_payment": "No",
                },
            ]
        }

        result = sort_obligations(build_obligations(data, as_of=datetime.date(2026, 9, 4)))

        assert result[0]["Account"] == "Open bill"
        assert result[1]["Account"] == "Paid bill"

    def test_due_date_orders_same_priority_items_deterministically(self):
        data = {
            "monthly_expenses": [
                {
                    "name": "Later bill",
                    "amount": 50.0,
                    "due_date": "2026-09-28",
                    "status": "not paid",
                    "critical_payment": "No",
                },
                {
                    "name": "Earlier bill",
                    "amount": 80.0,
                    "due_date": "2026-09-20",
                    "status": "not paid",
                    "critical_payment": "No",
                },
            ]
        }

        result = sort_obligations(build_obligations(data, as_of=datetime.date(2026, 9, 4)))

        assert result[0]["Account"] == "Earlier bill"
        assert result[1]["Account"] == "Later bill"

    def test_payment_status_behaviour_remains_intact(self):
        from app.data_store import FinanceDataStore

        card = FinanceDataStore().load()["credit_cards"][0]
        assert card["payment_status"] == "Not paid"

        overdue = {
            "credit_cards": [{
                "card_name": "Overdue Only",
                "credit_limit": 1000.0,
                "current_balance": 400.0,
                "statement_balance": 400.0,
                "statement_date": "2026-08-01",
                "payment_due_date": "2026-08-01",
                "minimum_payment_due": 50.0,
                "amount_paid_this_statement": 10.0,
                "remaining_statement_balance": 390.0,
                "apr": 18.0,
                "promotional_apr": 0.0,
                "interest_charged": 0.0,
                "direct_debit_enabled": "No",
                "payment_status": "Not paid",
                "notes": "",
            }]
        }

        from app.data_store import normalize_credit_card
        normalized = normalize_credit_card(overdue["credit_cards"][0])
        assert normalized["payment_status"] == "Overdue"
