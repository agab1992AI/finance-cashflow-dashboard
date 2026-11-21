"""Pure date-based cash-flow forecast calculations.

Caller contract:
- forecast_start is the date for the supplied spendable-cash balance.
- forecast_end is inclusive.
- starting_spendable_cash is the caller's confirmed spendable balance as of the start date.
- events contain only future, unpaid/scheduled cash flows known by the caller.
- Historical and already-paid obligations must not be passed or subtracted automatically.
- Amounts are cash-flow amounts: inflows are positive and outflows are negative.
- Savings are excluded from starting cash unless explicitly transferred into spendable cash.

This module never loads project data, assumes a pay-cycle length, or uses overdraft/savings
as spendable cash by default.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping, Optional, Union


DateValue = Union[date, datetime, str]


class ForecastValidationError(ValueError):
    """Raised when a forecast cannot be calculated safely from the supplied data."""


@dataclass(frozen=True)
class ForecastEvent:
    """A confirmed or explicitly scheduled future cash-flow event."""

    id: str
    date: DateValue
    amount: object
    type: str
    status: str = "unpaid"


def _parse_date(value: DateValue, field_name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ForecastValidationError(f"Missing or invalid date for {field_name}.")

    text = value.strip()
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    raise ForecastValidationError(f"Invalid date for {field_name}: {value!r}.")


def _money(value: object, field_name: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ForecastValidationError(f"Missing or invalid amount for {field_name}.")
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError, ValueError):
        raise ForecastValidationError(f"Invalid amount for {field_name}: {value!r}.")
    if not amount.is_finite():
        raise ForecastValidationError(f"Invalid amount for {field_name}: {value!r}.")
    return amount


def _paid_status(status: object) -> bool:
    text = str(status or "").strip().lower()
    return text in {"paid", "completed", "cleared", "fully paid", "received"}


def _event_as_dict(event: Union[ForecastEvent, Mapping]) -> dict:
    if isinstance(event, ForecastEvent):
        return {
            "id": event.id,
            "date": event.date,
            "amount": event.amount,
            "type": event.type,
            "status": event.status,
        }
    if isinstance(event, Mapping):
        return dict(event)
    raise ForecastValidationError("Each event must be a ForecastEvent or mapping.")


def calculate_cash_flow_forecast(
    forecast_start: DateValue,
    forecast_end: DateValue,
    starting_spendable_cash: object,
    events: Optional[Iterable[Union[ForecastEvent, Mapping]]] = None,
    savings_contribution: object = 0,
    available_savings_balance: object = 0,
    savings_transfer_date: Optional[DateValue] = None,
) -> dict:
    """Calculate a deterministic chronological cash forecast.

    The caller supplies spendable cash as at ``forecast_start`` and only future unpaid
    or scheduled events. The function does not infer income, subtract historical bills,
    include overdraft headroom, or treat savings as spendable cash.

    Returns running balances by date and the earliest cash shortfall. Savings transfers
    are represented once, dated explicitly, and excluded from income.
    """
    start = _parse_date(forecast_start, "forecast start")
    end = _parse_date(forecast_end, "forecast end")
    if end < start:
        raise ForecastValidationError("Forecast end date cannot be before forecast start date.")

    starting_cash = _money(starting_spendable_cash, "starting spendable cash")
    if starting_cash < 0:
        raise ForecastValidationError("Starting spendable cash balance cannot be negative.")

    contribution = _money(savings_contribution, "savings contribution")
    savings = _money(available_savings_balance, "available savings balance")
    if contribution < 0:
        raise ForecastValidationError("Savings contribution cannot be negative.")
    if savings < 0:
        raise ForecastValidationError("Available savings balance cannot be negative.")
    if contribution > savings:
        raise ForecastValidationError("Savings contribution cannot exceed the available savings balance.")

    normalized_events = []
    identifiers = set()

    for raw_event in events or []:
        event = _event_as_dict(raw_event)
        identifier = event.get("id")
        if identifier is None or not str(identifier).strip():
            raise ForecastValidationError("Each event requires a stable identifier.")
        identifier = str(identifier).strip()
        if identifier in identifiers:
            raise ForecastValidationError(f"Duplicate event identifier: {identifier}.")
        identifiers.add(identifier)

        event_status = str(event.get("status") or "").strip().lower()
        event_type = str(event.get("type") or "").strip().lower()

        if event_type in {"transfer", "internal_transfer", "savings_transfer"}:
            raise ForecastValidationError(
                f"Internal transfer event {identifier} must not be supplied separately; "
                "use the savings scenario parameters."
            )

        if _paid_status(event_status):
            continue

        event_date = _parse_date(event.get("date"), f"event {identifier}")
        amount = _money(event.get("amount"), f"event {identifier}")

        if event_date < start:
            raise ForecastValidationError(
                f"Event {identifier} is historical; only future unpaid events belong in this forecast."
            )
        if event_date > end:
            continue

        if amount == 0:
            raise ForecastValidationError(f"Event {identifier} must have a non-zero amount.")

        if event_type in {"income", "inflow", "confirmed_income", "scheduled_income"}:
            if event_status not in {"confirmed", "scheduled", "explicitly_scheduled"}:
                raise ForecastValidationError(
                    f"Inflows require confirmed or explicitly scheduled status: {identifier}."
                )
            if amount < 0:
                raise ForecastValidationError(f"Inflow event {identifier} must have a positive amount.")
            sort_rank = 0
        elif event_type in {"expense", "outflow", "bill", "loan_repayment", "card_minimum", "debt_repayment"}:
            if event_status in {"unknown", "missing", "unconfirmed"}:
                raise ForecastValidationError(f"Outflow event {identifier} is not explicitly unpaid/scheduled.")
            if amount > 0:
                raise ForecastValidationError(f"Outflow event {identifier} must have a negative amount.")
            sort_rank = 2
        else:
            raise ForecastValidationError(f"Unknown event type for {identifier}: {event_type!r}.")

        normalized_events.append((event_date, sort_rank, identifier, event_type, amount))

    if contribution > 0:
        if savings_transfer_date is None:
            raise ForecastValidationError("Savings transfer date is required when savings contribution is greater than zero.")
        transfer_date = _parse_date(savings_transfer_date, "savings transfer")
        if transfer_date < start or transfer_date > end:
            raise ForecastValidationError("Savings transfer date must fall within the forecast period.")

        transfer_id = "__savings_transfer__"
        if transfer_id in identifiers:
            raise ForecastValidationError("Duplicate event identifier: __savings_transfer__. ")
        normalized_events.append((transfer_date, 1, transfer_id, "savings_transfer", contribution))

    normalized_events.sort(key=lambda item: (item[0], item[1], item[2]))

    balances = []
    running_cash = starting_cash
    earliest_shortfall = None

    events_by_date = {}
    for event_date, _, identifier, event_type, amount in normalized_events:
        events_by_date.setdefault(event_date, []).append((identifier, event_type, amount))

    current = start
    while current <= end:
        day_events = events_by_date.get(current, [])
        for _, event_type, amount in day_events:
            running_cash += amount

        running_cash = running_cash.quantize(Decimal("0.01"))
        balances.append({"date": current, "balance": float(running_cash)})

        if earliest_shortfall is None and running_cash < 0:
            earliest_shortfall = current
        current += timedelta(days=1)

    remaining_savings = savings - contribution
    result = {
        "running_balances": balances,
        "earliest_shortfall": earliest_shortfall,
        "remaining_savings": float(remaining_savings.quantize(Decimal("0.01"))),
        "savings_transferred": float(contribution.quantize(Decimal("0.01"))),
        "events": normalized_events,
    }
    return result
