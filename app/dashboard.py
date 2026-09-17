from datetime import date, datetime

import customtkinter as ctk

from app.data_store import FinanceDataStore
from app.finance import FinanceSummary
from app.settings import APP_TITLE, APP_SUBTITLE, APP_THEME


SECTION_ORDER = [
    "Bank Accounts",
    "Savings",
    "Credit Cards",
    "Loans and Other Debts",
    "Income",
    "Bills & Regular Expenses",
    "Investments",
    "Financial Goals",
]


SECTION_CONFIG = {
    "Bank Accounts": {
        "key": "bank_accounts",
        "id_field": "name",
        "fields": [
            ("account_name", "Account name", "name"),
            ("current_balance", "Current balance", "balance"),
            ("overdraft_limit", "Overdraft limit", "overdraft_limit"),
            ("notes", "Notes", "notes"),
        ],
    },
    "Savings": {
        "key": "savings",
        "id_field": "name",
        "fields": [
            ("name", "Savings name", "name"),
            ("balance", "Current balance", "balance"),
            ("notes", "Notes", "notes"),
        ],
    },
    "Credit Cards": {
        "key": "credit_cards",
        "id_field": "card_name",
        "fields": [
            ("card_name", "Card name", "card_name"),
            ("credit_limit", "Credit limit", "credit_limit"),
            ("current_balance", "Current balance", "current_balance"),
            ("statement_balance", "Statement balance", "statement_balance"),
            ("statement_date", "Statement date", "statement_date"),
            ("payment_due_date", "Payment due date", "payment_due_date"),
            ("minimum_payment_due", "Minimum payment due", "minimum_payment_due"),
            ("amount_paid_this_statement", "Amount already paid this statement", "amount_paid_this_statement"),
            ("remaining_statement_balance", "Remaining statement balance", "remaining_statement_balance"),
            ("apr", "APR", "apr"),
            ("promotional_apr", "Promotional APR", "promotional_apr"),
            ("interest_charged", "Interest charged", "interest_charged"),
            ("direct_debit_enabled", "Direct debit enabled", "direct_debit_enabled"),
            ("payment_status", "Payment status", "payment_status"),
            ("notes", "Notes", "notes"),
        ],
    },
    "Loans and Other Debts": {
        "key": "loans",
        "id_field": "creditor",
        "fields": [
            ("creditor", "Creditor", "creditor"),
            ("debt_type", "Debt type", "debt_type"),
            ("current_balance", "Current balance", "current_balance"),
            ("monthly_payment", "Monthly payment", "monthly_payment"),
            ("due_date", "Due date", "due_date"),
            ("interest_or_fees", "Interest or fees", "interest_or_fees"),
            ("priority", "Priority", "priority"),
            ("notes", "Notes", "notes"),
        ],
    },
    "Income": {
        "key": "monthly_income",
        "id_field": "source",
        "fields": [
            ("source", "Source", "source"),
            ("amount", "Amount", "amount"),
            ("date", "Date", "date"),
            ("received_status", "Received status", "received_status"),
        ],
    },
    "Bills & Regular Expenses": {
        "key": "monthly_expenses",
        "id_field": "name",
        "fields": [
            ("name", "Name", "name"),
            ("amount", "Amount", "amount"),
            ("due_date", "Due date", "due_date"),
            ("account_used", "Account used", "account_used"),
            ("status", "Paid, pending or returned", "status"),
            ("critical_payment", "Critical payment yes or no", "critical_payment"),
            ("notes", "Notes", "notes"),
        ],
    },
    "Direct Debits": {
        "key": "direct_debits",
        "id_field": "name",
        "fields": [
            ("name", "Name", "name"),
            ("amount", "Amount", "amount"),
            ("due_date", "Due date", "due_date"),
            ("account_used", "Account used", "account_used"),
            ("status", "Paid, pending or returned", "status"),
            ("critical_payment", "Critical payment yes or no", "critical_payment"),
            ("notes", "Notes", "notes"),
        ],
    },
    "Investments": {
        "key": "investments",
        "id_field": "provider",
        "fields": [
            ("provider", "Provider", "provider"),
            ("cash_balance", "Cash balance", "cash_balance"),
            ("investment_value", "Investment value", "investment_value"),
            ("cashback", "Cashback", "cashback"),
            ("interest", "Interest", "interest"),
            ("dividends", "Dividends", "dividends"),
            ("notes", "Notes", "notes"),
        ],
    },
    "Financial Goals": {
        "key": "goals",
        "id_field": "goal_name",
        "fields": [
            ("goal_name", "Goal name", "goal_name"),
            ("target_amount", "Target amount", "target_amount"),
            ("current_amount", "Current amount", "current_amount"),
            ("target_date", "Target date", "target_date"),
            ("priority", "Priority", "priority"),
            ("notes", "Notes", "notes"),
        ],
    },
}


class DashboardApp:
    def __init__(self):
        ctk.set_appearance_mode(APP_THEME)
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title(APP_TITLE)
        self.root.geometry("1400x920")
        self.root.minsize(1100, 780)
        self.root.configure(fg_color="#0f172a")

        self.data_store = FinanceDataStore()
        self.data = self.data_store.load()
        self.finance = FinanceSummary(self.data)
        self.section_widgets = {}
        self.section_state = {}
        self.selected_tab = SECTION_ORDER[0]

        self._build_dashboard()

    def _current_tab_name(self):
        if hasattr(self, "tabview") and hasattr(self.tabview, "get"):
            try:
                return self.tabview.get()
            except Exception:
                pass
        return getattr(self, "selected_tab", SECTION_ORDER[0])

    def _build_dashboard(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self.root, corner_radius=20, fg_color="#111827")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        header = ctk.CTkLabel(
            main_frame,
            text=f"{APP_TITLE}\n{APP_SUBTITLE}",
            font=("Arial", 26, "bold"),
            justify="center",
            text_color="#e5e7eb",
        )
        header.grid(row=0, column=0, columnspan=2, pady=(20, 18), sticky="ew")

        self._build_metric_card(main_frame, "Total assets", f"£{self.finance.total_assets():,.2f}", 1, 0)
        self._build_metric_card(main_frame, "Total cash", f"£{self.finance.total_cash():,.2f}", 1, 1)
        self._build_metric_card(main_frame, "Total debt", f"£{self.finance.total_debt():,.2f}", 2, 0)
        self._build_metric_card(main_frame, "Net worth", f"£{self.finance.net_worth():,.2f}", 2, 1)
        self._build_metric_card(main_frame, "Available overdraft", f"£{self.finance.total_available_overdraft():,.2f}", 3, 0)
        self._build_metric_card(main_frame, "Goals remaining", f"£{self.finance.total_goals_remaining():,.2f}", 3, 1)

        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.grid(row=4, column=0, columnspan=2, padx=12, pady=12, sticky="nsew")

        for section_name in SECTION_ORDER:
            self.tabview.add(section_name)
        self.tabview.add("Review")
        self.selected_tab = self._current_tab_name()
        if self.selected_tab not in {"Review", *SECTION_ORDER}:
            self.selected_tab = SECTION_ORDER[0]
        self.tabview.set(self.selected_tab)

        self._build_section_tabs()
        self._build_review_tab()

        self.save_button = ctk.CTkButton(main_frame, text="Save all changes", command=self._save_and_refresh)
        self.save_button.grid(row=5, column=0, columnspan=2, padx=12, pady=(0, 16), sticky="ew")

    def _build_metric_card(self, parent, title, value, row, col):
        card = ctk.CTkFrame(parent, corner_radius=18, fg_color="#1f2937")
        card.grid(row=row, column=col, padx=12, pady=10, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=title, font=("Arial", 14, "bold"), text_color="#93c5fd").grid(
            row=0, column=0, padx=16, pady=(14, 4), sticky="w"
        )
        ctk.CTkLabel(card, text=value, font=("Arial", 22, "bold"), text_color="#f8fafc").grid(
            row=1, column=0, padx=16, pady=(0, 16), sticky="w"
        )

    def _build_section_tabs(self):
        for section_name in SECTION_ORDER:
            config = SECTION_CONFIG[section_name]
            parent = self.tabview.tab(section_name)
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(0, weight=2)
            parent.grid_columnconfigure(1, weight=1)

            form_frame = ctk.CTkScrollableFrame(parent, corner_radius=16, fg_color="#111827")
            form_frame.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
            form_frame.grid_columnconfigure(0, weight=0)
            form_frame.grid_columnconfigure(1, weight=1)

            list_frame = ctk.CTkFrame(parent, corner_radius=16, fg_color="#111827")
            list_frame.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="nsew")
            list_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(list_frame, text="Stored entries", font=("Arial", 15, "bold"), text_color="#f8fafc").grid(
                row=0, column=0, padx=10, pady=(10, 8), sticky="w"
            )

            choices = self._existing_entries_for_section(config["key"], config["id_field"])
            selection_var = ctk.StringVar(value=choices[0] if choices else "")
            selection_menu = ctk.CTkOptionMenu(list_frame, values=choices or ["No items"], variable=selection_var)
            selection_menu.grid(row=1, column=0, padx=10, pady=6, sticky="ew")
            selection_menu.configure(command=lambda value, sec=section_name: self._load_selected_entry(sec, value))

            budget_used_var = ctk.StringVar(value="Overdraft used: £0.00")
            budget_available_var = ctk.StringVar(value="Available overdraft: £0.00")
            credit_status_var = ctk.StringVar(value="Card status:")
            credit_warning_var = ctk.StringVar(value="")
            credit_status_label = None
            credit_warning_label = None
            if section_name == "Bank Accounts":
                ctk.CTkLabel(list_frame, textvariable=budget_used_var, font=("Arial", 12, "bold"), text_color="#cbd5e1").grid(
                    row=2, column=0, padx=10, pady=(6, 2), sticky="w"
                )
                ctk.CTkLabel(list_frame, textvariable=budget_available_var, font=("Arial", 12, "bold"), text_color="#cbd5e1").grid(
                    row=3, column=0, padx=10, pady=(2, 10), sticky="w"
                )
            if section_name == "Credit Cards":
                credit_status_label = ctk.CTkLabel(list_frame, textvariable=credit_status_var, font=("Arial", 12, "bold"), text_color="#cbd5e1")
                credit_status_label.grid(row=2, column=0, padx=10, pady=(6, 2), sticky="w")
                credit_warning_label = ctk.CTkLabel(list_frame, textvariable=credit_warning_var, font=("Arial", 12, "bold"), text_color="#fcd34d")
                credit_warning_label.grid(row=3, column=0, padx=10, pady=(2, 10), sticky="w")

            form_vars = {}
            for row_index, (field_key, label, data_key) in enumerate(config["fields"]):
                ctk.CTkLabel(form_frame, text=label, font=("Arial", 12, "bold"), text_color="#cbd5e1").grid(
                    row=row_index, column=0, padx=12, pady=(10, 4), sticky="w"
                )
                value = ""
                widget_var = ctk.StringVar(value=value)
                form_vars[data_key] = widget_var

                if data_key == "notes":
                    entry = ctk.CTkTextbox(form_frame, width=420, height=90)
                    entry.grid(row=row_index, column=1, padx=12, pady=(6, 6), sticky="ew")
                    form_vars[f"{data_key}_entry"] = entry
                else:
                    entry = ctk.CTkEntry(form_frame, width=320, textvariable=widget_var)
                    entry.grid(row=row_index, column=1, padx=12, pady=(6, 6), sticky="ew")
                    form_vars[data_key] = widget_var

            button_frame = ctk.CTkFrame(form_frame, corner_radius=12, fg_color="#0f172a")
            button_frame.grid(row=len(config["fields"]), column=0, columnspan=2, padx=12, pady=(12, 16), sticky="ew")
            button_frame.grid_columnconfigure(0, weight=1)
            button_frame.grid_columnconfigure(1, weight=1)
            button_frame.grid_columnconfigure(2, weight=1)
            button_frame.grid_columnconfigure(3, weight=1)

            ctk.CTkButton(button_frame, text="Add", command=lambda s=section_name: self._add_section_entry(s)).grid(row=0, column=0, padx=6, pady=8, sticky="ew")
            ctk.CTkButton(button_frame, text="Edit", command=lambda s=section_name, v=selection_var: self._edit_section_entry(s, v)).grid(row=0, column=1, padx=6, pady=8, sticky="ew")
            ctk.CTkButton(button_frame, text="Delete", command=lambda s=section_name, v=selection_var: self._delete_section_entry(s, v)).grid(row=0, column=2, padx=6, pady=8, sticky="ew")
            ctk.CTkButton(button_frame, text="Save", command=lambda s=section_name, v=selection_var: self._save_section_entry(s, v)).grid(row=0, column=3, padx=6, pady=8, sticky="ew")

            self.section_widgets[section_name] = {
                "form": form_frame,
                "selection_var": selection_var,
                "selection_menu": selection_menu,
                "vars": form_vars,
                "config": config,
                "read_only_used": budget_used_var if section_name == "Bank Accounts" else None,
                "read_only_available": budget_available_var if section_name == "Bank Accounts" else None,
                "credit_status": credit_status_var if section_name == "Credit Cards" else None,
                "credit_warning_text": credit_warning_var if section_name == "Credit Cards" else None,
                "credit_status_label": credit_status_label if section_name == "Credit Cards" else None,
                "credit_warning_label": credit_warning_label if section_name == "Credit Cards" else None,
            }
            self.section_state[section_name] = {"editing_index": None}

    def _build_review_tab(self):
        review_parent = self.tabview.tab("Review")
        review_parent.grid_columnconfigure(0, weight=1)
        review_parent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(review_parent, text="Review your local JSON data before saving", font=("Arial", 16, "bold"), text_color="#f8fafc").grid(
            row=0, column=0, padx=12, pady=(12, 8), sticky="w"
        )

        self.review_box = ctk.CTkTextbox(review_parent, width=1200, height=520, fg_color="#0f172a", text_color="#e5e7eb")
        self.review_box.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.review_box.insert("0.0", self._render_review_text())
        self.review_box.configure(state="disabled")

        ctk.CTkButton(review_parent, text="Refresh review", command=self._refresh_review_screen).grid(
            row=2, column=0, padx=12, pady=(0, 12), sticky="ew"
        )

    def _add_section_entry(self, section_name):
        config = SECTION_CONFIG[section_name]
        item = self._read_form_values(section_name)
        if not item:
            return
        if section_name == "Bank Accounts":
            item = self._normalize_bank_account(item)
            if item is None:
                return
        if section_name == "Credit Cards":
            item = self._normalize_credit_card(item)
        self.data.setdefault(config["key"], []).append(item)
        self.section_state[section_name]["editing_index"] = None
        self.selected_tab = section_name
        self.data_store.save(self.data)
        self._refresh_dashboard(section_name)

    def _load_selected_entry(self, section_name, selected_label):
        config = SECTION_CONFIG[section_name]
        key = config["key"]
        if not selected_label or selected_label == "No items":
            return

        for index, item in enumerate(self.data.get(key, [])):
            if self._item_label(item, config["id_field"]) == selected_label:
                self.section_state[section_name]["editing_index"] = index
                self._populate_form(section_name, item)
                return

    def _edit_section_entry(self, section_name, selection_var):
        self._load_selected_entry(section_name, selection_var.get())

    def _delete_section_entry(self, section_name, selection_var):
        config = SECTION_CONFIG[section_name]
        key = config["key"]
        items = self.data.get(key, [])
        selected_label = selection_var.get()
        for index, item in enumerate(items):
            if self._item_label(item, config["id_field"]) == selected_label:
                items.pop(index)
                self.selected_tab = section_name
                self.data_store.save(self.data)
                self._reload_dashboard(section_name)
                return

    def _save_section_entry(self, section_name, selection_var, refresh=True):
        config = SECTION_CONFIG[section_name]
        key = config["key"]
        item = self._read_form_values(section_name)
        if not item:
            return

        if section_name == "Bank Accounts":
            item = self._normalize_bank_account(item)
            if item is None:
                return
        if section_name == "Credit Cards":
            item = self._normalize_credit_card(item)

        index = self.section_state[section_name]["editing_index"]
        if index is None:
            self.data.setdefault(key, []).append(item)
        else:
            if 0 <= index < len(self.data.get(key, [])):
                self.data[key][index] = item

        self.selected_tab = section_name
        self.data_store.save(self.data)
        if refresh:
            self._reload_dashboard(section_name)

    def _read_form_values(self, section_name):
        widgets = self.section_widgets[section_name]
        data = {}
        for _, label, data_key in widgets["config"]["fields"]:
            if data_key == "notes":
                text_widget = widgets["vars"].get(f"{data_key}_entry")
                if text_widget is not None:
                    data[data_key] = text_widget.get("0.0", "end").strip()
                else:
                    data[data_key] = ""
            else:
                widget_var = widgets["vars"].get(data_key)
                value = widget_var.get().strip() if widget_var is not None else ""
                data[data_key] = value
        return data

    def _has_section_form_data(self, section_name):
        values = self._read_form_values(section_name).values()
        return any(str(value).strip() for value in values)

    def _populate_form(self, section_name, item):
        widgets = self.section_widgets[section_name]
        for _, _, data_key in widgets["config"]["fields"]:
            if data_key == "notes":
                textbox = widgets["vars"].get(f"{data_key}_entry")
                if textbox is not None:
                    textbox.delete("0.0", "end")
                    textbox.insert("0.0", str(item.get(data_key, "")))
            else:
                widgets["vars"][data_key].set(str(item.get(data_key, "")))

        if section_name == "Bank Accounts":
            derived = self._derive_bank_overdraft(item)
            widgets["read_only_used"].set(f"Overdraft used: £{derived['overdraft_used']:.2f}")
            widgets["read_only_available"].set(f"Available overdraft: £{derived['available_overdraft']:.2f}")

        if section_name == "Credit Cards":
            status, notice, color = self._credit_card_dashboard_status(item)
            widgets["credit_status"].set(f"Card status: {status}")
            widgets["credit_warning_text"].set(notice)
            widgets["credit_warning_label"].configure(text_color=color)

    def _normalize_bank_account(self, item):
        try:
            balance = float(item.get("balance", 0.0))
            overdraft_limit = float(item.get("overdraft_limit", 0.0))
        except (TypeError, ValueError):
            return None

        if overdraft_limit < 0:
            return None

        derived = self._derive_bank_overdraft({"balance": balance, "overdraft_limit": overdraft_limit})
        item["overdraft_used"] = derived["overdraft_used"]
        item["available_overdraft"] = derived["available_overdraft"]
        return item

    def _normalize_credit_card(self, item):
        try:
            current_balance = float(item.get("current_balance", 0.0))
            statement_balance = float(item.get("statement_balance", current_balance))
            minimum_payment_due = float(item.get("minimum_payment_due", 0.0))
            amount_paid_this_statement = float(item.get("amount_paid_this_statement", 0.0))
            credit_limit = float(item.get("credit_limit", 0.0))
        except (TypeError, ValueError):
            return item

        remaining_statement_balance = max(statement_balance - amount_paid_this_statement, 0.0)
        direct_debit_enabled = str(item.get("direct_debit_enabled", "No")).strip().lower()
        direct_debit_enabled = "Yes" if direct_debit_enabled in {"yes", "y", "true", "1"} else "No"

        if amount_paid_this_statement >= statement_balance:
            payment_status = "Fully paid"
        elif minimum_payment_due > 0 and amount_paid_this_statement >= minimum_payment_due:
            payment_status = "Minimum paid"
        else:
            payment_status = "Not paid"

        item.update(
            {
                "card_name": str(item.get("card_name") or item.get("name") or "Credit card").strip(),
                "credit_limit": credit_limit,
                "current_balance": current_balance,
                "statement_balance": statement_balance,
                "statement_date": str(item.get("statement_date") or "2026-08-01").strip(),
                "payment_due_date": str(item.get("payment_due_date") or item.get("payment_date") or "2026-08-18").strip(),
                "minimum_payment_due": minimum_payment_due,
                "amount_paid_this_statement": amount_paid_this_statement,
                "remaining_statement_balance": round(remaining_statement_balance, 2),
                "apr": float(item.get("apr", 0.0) or 0.0),
                "promotional_apr": float(item.get("promotional_apr", 0.0) or 0.0),
                "interest_charged": float(item.get("interest_charged", 0.0) or 0.0),
                "direct_debit_enabled": direct_debit_enabled,
                "payment_status": payment_status,
                "notes": str(item.get("notes", "")).strip(),
            }
        )
        return item

    def _derive_bank_overdraft(self, item):
        try:
            balance = float(item.get("balance", 0.0))
            overdraft_limit = float(item.get("overdraft_limit", 0.0))
        except (TypeError, ValueError):
            return {"overdraft_used": 0.0, "available_overdraft": 0.0}

        if overdraft_limit < 0:
            overdraft_limit = 0.0

        if balance >= 0:
            overdraft_used = 0.0
            available_overdraft = overdraft_limit
        else:
            overdraft_used = min(abs(balance), overdraft_limit)
            available_overdraft = max(0.0, overdraft_limit - overdraft_used)

        return {
            "overdraft_used": round(overdraft_used, 2),
            "available_overdraft": round(available_overdraft, 2),
        }

    def _render_review_text(self):
        lines = ["CashFlow AI - guided review snapshot"]
        for section_name in SECTION_ORDER:
            key = SECTION_CONFIG[section_name]["key"]
            lines.append(f"\n{section_name}:")
            entries = self.data.get(key, [])
            if not entries:
                lines.append("  - no entries")
                continue
            for entry in entries:
                if section_name == "Bank Accounts":
                    derived = self._derive_bank_overdraft(entry)
                    entry = dict(entry)
                    entry["overdraft_used"] = derived["overdraft_used"]
                    entry["available_overdraft"] = derived["available_overdraft"]
                if section_name == "Credit Cards":
                    entry = dict(entry)
                    entry["remaining_statement_balance"] = self._remaining_statement_balance(entry)
                    entry["payment_status"] = self._payment_status(entry)
                summary = ", ".join([f"{k}: {v}" for k, v in entry.items()])
                lines.append(f"  - {summary}")
        return "\n".join(lines)

    def _refresh_review_screen(self):
        self.review_box.configure(state="normal")
        self.review_box.delete("0.0", "end")
        self.review_box.insert("0.0", self._render_review_text())
        self.review_box.configure(state="disabled")

    def _existing_entries_for_section(self, key, id_field):
        items = self.data.get(key, [])
        labels = []
        for item in items:
            label = self._item_label(item, id_field)
            if label:
                labels.append(label)
        return labels

    def _item_label(self, item, id_field):
        if id_field in item:
            return str(item.get(id_field, ""))
        if "name" in item:
            return str(item.get("name", ""))
        return ""

    def _refresh_dashboard(self, selected_tab=None):
        if hasattr(self, "data_store"):
            self.data = self.data_store.load()
        self.finance = FinanceSummary(self.data)
        self.selected_tab = selected_tab or getattr(self, "selected_tab", SECTION_ORDER[0]) or SECTION_ORDER[0]
        if hasattr(self, "root"):
            for child in self.root.winfo_children():
                child.destroy()
        if hasattr(self, "_build_dashboard"):
            self._build_dashboard()
        if selected_tab is not None and hasattr(self, "tabview") and hasattr(self.tabview, "set"):
            self.selected_tab = selected_tab
            try:
                self.tabview.set(selected_tab)
            except Exception:
                pass

    def _reload_dashboard(self, selected_tab=None):
        if hasattr(self, "data_store"):
            self.data = self.data_store.load()
        self.finance = FinanceSummary(self.data)
        self.selected_tab = selected_tab or getattr(self, "selected_tab", SECTION_ORDER[0]) or SECTION_ORDER[0]
        if hasattr(self, "root"):
            for child in self.root.winfo_children():
                child.destroy()
        if hasattr(self, "_build_dashboard"):
            self._build_dashboard()
        if selected_tab is not None and hasattr(self, "tabview") and hasattr(self.tabview, "set"):
            self.selected_tab = selected_tab
            try:
                self.tabview.set(selected_tab)
            except Exception:
                pass

    def _save_all_form_data(self):
        current_tab = self._current_tab_name()
        self.selected_tab = current_tab

        if not hasattr(self, "section_widgets"):
            self.data_store.save(self.data)
            return

        for section_name in SECTION_ORDER:
            if section_name not in self.section_widgets:
                continue
            if self._has_section_form_data(section_name):
                self._save_section_entry(section_name, self.section_widgets[section_name].get("selection_var"), refresh=False)

        self.selected_tab = current_tab
        self.data_store.save(self.data)

    def _save_and_refresh(self):
        selected_tab = self._current_tab_name()
        self._save_all_form_data()
        self._refresh_dashboard(selected_tab)

    def _remaining_statement_balance(self, card):
        try:
            statement_balance = float(card.get("statement_balance", 0.0))
            amount_paid = float(card.get("amount_paid_this_statement", 0.0))
        except (TypeError, ValueError):
            return 0.0
        return round(max(statement_balance - amount_paid, 0.0), 2)

    def _payment_status(self, card):
        remaining = self._remaining_statement_balance(card)
        minimum_payment = float(card.get("minimum_payment_due", 0.0) or 0.0)
        amount_paid = float(card.get("amount_paid_this_statement", 0.0) or 0.0)
        due_date = str(card.get("payment_due_date") or "").strip()

        try:
            if due_date and datetime.strptime(due_date, "%Y-%m-%d").date() < date.today() and remaining > 0:
                if amount_paid < minimum_payment:
                    return "Overdue"
        except (TypeError, ValueError):
            pass

        if remaining <= 0:
            return "Fully paid"
        if minimum_payment > 0 and amount_paid >= minimum_payment:
            return "Minimum paid"
        return "Not paid"

    def _credit_card_dashboard_status(self, card):
        status = self._payment_status(card)
        remaining = self._remaining_statement_balance(card)
        minimum_payment = float(card.get("minimum_payment_due", 0.0) or 0.0)
        amount_paid = float(card.get("amount_paid_this_statement", 0.0) or 0.0)
        due_date = str(card.get("payment_due_date") or "").strip()

        due_message = f"Remaining before due date: £{remaining:.2f}"
        warning_color = "#f8fafc"
        notice = due_message

        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
            days_remaining = (due_date_obj - date.today()).days
            if days_remaining <= 7 and remaining > 0:
                warning_color = "#fcd34d"
                notice = f"Due in {days_remaining} day(s) • {due_message}"
            if due_date_obj < date.today() and remaining > 0:
                warning_color = "#f87171"
                notice = f"Overdue • {due_message}"
        except (TypeError, ValueError):
            pass

        if status == "Minimum paid":
            warning_color = "#34d399"
            notice = f"Minimum paid • {due_message}"
        elif status == "Fully paid":
            warning_color = "#93c5fd"
            notice = f"Fully paid • £0.00 remaining before due date"

        return status, notice, warning_color

    def run(self):
        self.root.mainloop()

