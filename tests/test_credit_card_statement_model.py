import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta

from app.dashboard import DashboardApp, SECTION_CONFIG
from app.data_store import FinanceDataStore


class CreditCardStatementModelTests(unittest.TestCase):
    def test_credit_card_defaults_include_statement_cycle_fields(self):
        default_data = FinanceDataStore().load()
        card = default_data["credit_cards"][0]

        self.assertIn("card_name", card)
        self.assertIn("credit_limit", card)
        self.assertIn("current_balance", card)
        self.assertIn("statement_balance", card)
        self.assertIn("statement_date", card)
        self.assertIn("payment_due_date", card)
        self.assertIn("minimum_payment_due", card)
        self.assertIn("amount_paid_this_statement", card)
        self.assertIn("remaining_statement_balance", card)
        self.assertIn("apr", card)
        self.assertIn("promotional_apr", card)
        self.assertIn("interest_charged", card)
        self.assertIn("direct_debit_enabled", card)
        self.assertIn("payment_status", card)
        self.assertIn("notes", card)

    def test_credit_card_statement_balance_is_derived_from_paid_amount(self):
        future_due = (date.today() + timedelta(days=14)).isoformat()

        data = {
            "credit_cards": [
                {
                    "card_name": "HSBC",
                    "credit_limit": 3000.0,
                    "current_balance": 430.0,
                    "statement_balance": 420.0,
                    "statement_date": "2026-08-01",
                    "payment_due_date": future_due,
                    "minimum_payment_due": 25.0,
                    "amount_paid_this_statement": 20.0,
                    "remaining_statement_balance": 0.0,
                    "apr": 22.9,
                    "promotional_apr": 0.0,
                    "interest_charged": 0.0,
                    "direct_debit_enabled": "Yes",
                    "payment_status": "Not paid",
                    "notes": "Statement cycle",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "finance_data.json"
            store = FinanceDataStore(str(json_path))
            store.save(data)
            migrated = store.load()

            card = migrated["credit_cards"][0]
            self.assertEqual(card["remaining_statement_balance"], 400.0)
            self.assertEqual(card["payment_status"], "Not paid")

    def test_load_migrates_legacy_credit_card_entry_to_statement_cycle_schema(self):
        legacy_data = {
            "credit_cards": [
                {"name": "Legacy Card", "balance": 150.0}
            ]
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "finance_data.json"
            store = FinanceDataStore(str(json_path))
            store.save(legacy_data)

            loaded = store.load()
            card = loaded["credit_cards"][0]

            self.assertEqual(card["card_name"], "Legacy Card")
            self.assertEqual(card["current_balance"], 150.0)
            self.assertEqual(card["statement_balance"], 150.0)
            self.assertEqual(card["remaining_statement_balance"], 150.0)
            self.assertEqual(card["payment_status"], "Not paid")

    def test_save_all_form_data_persists_credit_card_entry(self):
        app = DashboardApp.__new__(DashboardApp)
        app.data = {"bank_accounts": [{"name": "Main", "balance": 2000.0}], "credit_cards": []}
        app.section_state = {"Credit Cards": {"editing_index": None}}
        app.selected_tab = "Credit Cards"
        app.tabview = type("DummyTabview", (), {"get": lambda self: "Credit Cards"})()
        app.data_store = type("DummyStore", (), {"save": lambda self, data: setattr(app, "saved_data", data)})()
        app.section_widgets = {
            "Credit Cards": {
                "selection_var": None,
                "config": SECTION_CONFIG["Credit Cards"],
                "vars": {
                    "card_name": type("DummyVar", (), {"get": lambda self: "New Card"})(),
                    "credit_limit": type("DummyVar", (), {"get": lambda self: "2500"})(),
                    "current_balance": type("DummyVar", (), {"get": lambda self: "420"})(),
                    "statement_balance": type("DummyVar", (), {"get": lambda self: "420"})(),
                    "statement_date": type("DummyVar", (), {"get": lambda self: "2026-08-01"})(),
                    "payment_due_date": type("DummyVar", (), {"get": lambda self: "2026-08-18"})(),
                    "minimum_payment_due": type("DummyVar", (), {"get": lambda self: "35"})(),
                    "amount_paid_this_statement": type("DummyVar", (), {"get": lambda self: "20"})(),
                    "remaining_statement_balance": type("DummyVar", (), {"get": lambda self: "400"})(),
                    "apr": type("DummyVar", (), {"get": lambda self: "18.9"})(),
                    "promotional_apr": type("DummyVar", (), {"get": lambda self: "0"})(),
                    "interest_charged": type("DummyVar", (), {"get": lambda self: "0"})(),
                    "direct_debit_enabled": type("DummyVar", (), {"get": lambda self: "Yes"})(),
                    "payment_status": type("DummyVar", (), {"get": lambda self: "Not paid"})(),
                    "notes": type("DummyVar", (), {"get": lambda self: "Seasonal card"})(),
                },
            }
        }

        app._save_all_form_data()

        self.assertEqual(len(app.data["credit_cards"]), 1)
        self.assertEqual(app.data["credit_cards"][0]["card_name"], "New Card")
        self.assertEqual(app.data["credit_cards"][0]["payment_status"], "Not paid")

    def test_reload_dashboard_keeps_current_tab_selected(self):
        app = DashboardApp.__new__(DashboardApp)
        app.data = {"bank_accounts": [{"name": "Main", "balance": 2000.0}], "credit_cards": []}
        app.finance = object()
        app.selected_tab = "Credit Cards"
        app.tabview = type("DummyTabview", (), {"get": lambda self: "Credit Cards", "set": lambda self, value: setattr(self, "active", value), "active": "Credit Cards"})()
        app.root = type("DummyRoot", (), {"winfo_children": lambda self: []})()
        app.data_store = type("DummyStore", (), {"load": lambda self: {"bank_accounts": [{"name": "Main", "balance": 2000.0}], "credit_cards": []}})()
        app._build_dashboard = lambda: None

        app._reload_dashboard()

        self.assertEqual(app.selected_tab, "Credit Cards")


if __name__ == "__main__":
    unittest.main()
