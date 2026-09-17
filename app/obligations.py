import datetime
from typing import Any, Dict, List


def parse_date(date_str: str):
    if not date_str:
        return None
    # support multiple known formats present in data
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except Exception:
            continue
    return None


def money_or_unknown(value: Any):
    if value is None or value == "" or value == "unknown":
        return "Unknown"
    return value


def build_obligations(data: Dict, as_of: datetime.date = None) -> List[Dict]:
    """
    Build a list of obligation/risk items from provided finance data.

    Each item is a dict containing:
      Account | Amount | Status | Due/Promise Date | Priority | Reason

    Rules strictly derive only from stored fields. Unknowns remain 'Unknown'.
    """
    if as_of is None:
        as_of = datetime.date.today()

    obligations: List[Dict] = []

    # 1) Bank accounts - overdraft utilisation / low funds
    for acc in data.get("bank_accounts", []):
        name = acc.get("name") or acc.get("notes") or "Bank Account"
        balance = acc.get("balance")
        od_limit = acc.get("overdraft_limit")
        od_used = acc.get("overdraft_used")
        available_od = acc.get("available_overdraft")

        # Overdraft utilisation item
        if od_limit and od_limit > 0:
            status = f"Overdraft used: {money_or_unknown(od_used)}"
            due = "N/A"
            reason = f"Overdraft limit {od_limit}; headroom {money_or_unknown(available_od)}"
            # treat near-zero headroom as MONITOR (not inventing thresholds)
            priority = "MONITOR"
            obligations.append({
                "Account": name,
                "Amount": money_or_unknown(od_used),
                "Status": status,
                "Due/Promise Date": due,
                "Priority": priority,
                "Reason": reason,
            })
        else:
            # check low available balance
            if balance is not None and balance <= 25:
                obligations.append({
                    "Account": name,
                    "Amount": money_or_unknown(balance),
                    "Status": "Low available balance",
                    "Due/Promise Date": "Unknown",
                    "Priority": "MONITOR",
                    "Reason": "Low cash balance / no overdraft",
                })

    # 2) Credit cards - overdue, unpaid minimums, over limit, low available credit
    for card in data.get("credit_cards", []):
        name = card.get("card_name")
        current_balance = card.get("current_balance")
        credit_limit = card.get("credit_limit")
        min_due = card.get("minimum_payment_due")
        amount_paid = card.get("amount_paid_this_statement")
        payment_status = (card.get("payment_status") or "").strip()
        due_date = card.get("payment_due_date") or "Unknown"

        # exceeded limit
        if credit_limit is not None and current_balance is not None and current_balance > credit_limit:
            obligations.append({
                "Account": name,
                "Amount": f"{current_balance}",
                "Status": "Over credit limit",
                "Due/Promise Date": due_date,
                "Priority": "CRITICAL",
                "Reason": f"Current balance {current_balance} exceeds limit {credit_limit}",
            })

        # overdue / unpaid statement
        if payment_status and payment_status.upper().find("OVERDUE") >= 0:
            obligations.append({
                "Account": name,
                "Amount": money_or_unknown(card.get("remaining_statement_balance") or current_balance),
                "Status": payment_status,
                "Due/Promise Date": due_date,
                "Priority": "CRITICAL",
                "Reason": "Recorded overdue payment",
            })

        # unpaid minimum payment (only if min_due > 0 and not already paid)
        if min_due and min_due > 0:
            paid_enough = (amount_paid or 0) >= min_due
            if not paid_enough and ("PAID" not in (payment_status or "").upper()):
                # if there's a promise-to-pay mention, treat as HIGH unless already over limit/overdue
                priority = "HIGH"
                if "PROMISE" in (payment_status or "").upper():
                    priority = "HIGH"
                obligations.append({
                    "Account": name,
                    "Amount": min_due,
                    "Status": "Minimum payment unpaid",
                    "Due/Promise Date": due_date,
                    "Priority": priority,
                    "Reason": payment_status or "Minimum unpaid",
                })

        # low available credit
        if credit_limit is not None and current_balance is not None:
            available_credit = credit_limit - current_balance
            if available_credit <= 0:
                # already handled as over-limit above
                pass
            elif available_credit <= 50:
                obligations.append({
                    "Account": name,
                    "Amount": available_credit,
                    "Status": "Low available credit",
                    "Due/Promise Date": "Unknown",
                    "Priority": "MONITOR",
                    "Reason": f"Available credit {available_credit}",
                })

    # 3) Loans and other debts
    for loan in data.get("loans", []):
        creditor = loan.get("creditor")
        balance = loan.get("current_balance")
        payment_status = (loan.get("payment_status") or "").upper()
        balance_confidence = loan.get("balance_confidence")
        due_date = loan.get("due_date") or "Unknown"

        if payment_status and payment_status.find("RETURNED") >= 0:
            obligations.append({
                "Account": creditor,
                "Amount": money_or_unknown(loan.get("monthly_payment") or loan.get("current_balance")),
                "Status": "Returned / Unpaid",
                "Due/Promise Date": due_date,
                "Priority": "CRITICAL",
                "Reason": "Returned payment recorded and remains unpaid",
            })

        if balance_confidence and balance_confidence == "needs_verification":
            obligations.append({
                "Account": creditor,
                "Amount": money_or_unknown(balance),
                "Status": "Needs verification",
                "Due/Promise Date": due_date,
                "Priority": "VERIFY",
                "Reason": "Stored balance or due date requires verification",
            })

    # 4) payments_pending - returned/failed payments
    for p in data.get("payments_pending", []):
        if p.get("type") in ("returned_payment", "failed_payment") or p.get("status") == "returned":
            obligations.append({
                "Account": p.get("name") or "Pending Payment",
                "Amount": money_or_unknown(p.get("amount")),
                "Status": "Returned / Unpaid",
                "Due/Promise Date": "Unknown",
                "Priority": "CRITICAL",
                "Reason": "Returned payment remains unpaid",
            })

    # 5) monthly_expenses - not paid
    for exp in data.get("monthly_expenses", []):
        status = (exp.get("status") or "").lower()
        if status in ("not paid", "pending"):
            due_str = exp.get("due_date") or "Unknown"
            # try parse to determine overdue
            parsed = parse_date(due_str)
            priority = "HIGH"
            if parsed and parsed < as_of:
                priority = "CRITICAL"
            elif exp.get("critical_payment"):
                if str(exp.get("critical_payment")).lower() == "yes":
                    priority = "CRITICAL"
            obligations.append({
                "Account": exp.get("name"),
                "Amount": money_or_unknown(exp.get("amount")),
                "Status": exp.get("status"),
                "Due/Promise Date": due_str,
                "Priority": priority,
                "Reason": "Scheduled expense not marked paid",
            })

    return obligations


def summary_counts(obligations: List[Dict]) -> Dict[str, int]:
    counts = {"CRITICAL": 0, "HIGH": 0, "VERIFY": 0, "MONITOR": 0}
    for o in obligations:
        p = o.get("Priority")
        if p in counts:
            counts[p] += 1
    return counts


if __name__ == "__main__":
    import json
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1]
    data_file = root / "data" / "finance_data.json"
    with data_file.open() as f:
        data = json.load(f)

    obligs = build_obligations(data, as_of=datetime.date(2026, 9, 4))
    from pprint import pprint

    pprint(summary_counts(obligs))
    pprint(obligs)
