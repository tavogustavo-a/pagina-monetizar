"""Planes de membresía y catálogo de medios de pago."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

PLAN_GUEST = "guest"
PLAN_STANDARD = "standard"
PLAN_PLUS = "plus"
PLAN_ENTERPRISE = "enterprise"
PLAN_PREMIUM = "premium"
PLAN_ULTRA = "ultra"

PLANS: tuple[dict[str, Any], ...] = (
    {
        "id": PLAN_GUEST,
        "price_usd": 0,
        "videos": 15,
        "stats": 20,
        "invite_only": True,
        "featured": False,
        "sort": 0,
        "accent": "guest",
    },
    {
        "id": PLAN_STANDARD,
        "price_usd": 10,
        "videos": 50,
        "stats": 50,
        "invite_only": False,
        "featured": False,
        "sort": 1,
        "accent": "standard",
    },
    {
        "id": PLAN_PLUS,
        "price_usd": 20,
        "videos": 130,
        "stats": 150,
        "invite_only": False,
        "featured": False,
        "sort": 2,
        "accent": "plus",
    },
    {
        "id": PLAN_ENTERPRISE,
        "price_usd": 50,
        "videos": 250,
        "stats": 400,
        "invite_only": False,
        "featured": True,
        "sort": 3,
        "accent": "enterprise",
    },
    {
        "id": PLAN_PREMIUM,
        "price_usd": 100,
        "videos": 750,
        "stats": 1000,
        "invite_only": False,
        "featured": False,
        "sort": 4,
        "accent": "premium",
    },
    {
        "id": PLAN_ULTRA,
        "price_usd": 150,
        "videos": 1100,
        "stats": 1500,
        "invite_only": False,
        "featured": False,
        "sort": 5,
        "accent": "ultra",
    },
)

PLAN_IDS = frozenset(p["id"] for p in PLANS)
PAID_PLAN_IDS = frozenset(p["id"] for p in PLANS if not p["invite_only"])

PAYMENT_KINDS: tuple[dict[str, str], ...] = (
    {
        "id": "binance_pay",
        "icon": "🟡",
        "label_key": "pagos.kind.binance_pay",
    },
    {
        "id": "binance_transfer",
        "icon": "🪙",
        "label_key": "pagos.kind.binance_transfer",
    },
    {
        "id": "usdt_trc20",
        "icon": "💠",
        "label_key": "pagos.kind.usdt_trc20",
    },
    {
        "id": "usdt_bep20",
        "icon": "🔶",
        "label_key": "pagos.kind.usdt_bep20",
    },
    {
        "id": "stripe",
        "icon": "💳",
        "label_key": "pagos.kind.stripe",
    },
    {
        "id": "paypal",
        "icon": "🔵",
        "label_key": "pagos.kind.paypal",
    },
    {
        "id": "wise",
        "icon": "💚",
        "label_key": "pagos.kind.wise",
    },
    {
        "id": "custom",
        "icon": "✦",
        "label_key": "pagos.kind.custom",
    },
)

PAYMENT_KIND_IDS = frozenset(k["id"] for k in PAYMENT_KINDS)

PURCHASE_STATUSES = frozenset({"pending", "paid", "rejected", "cancelled"})
WALLET_METHOD_ID = "wallet"
BILLING_PERIOD_DAYS = 30


def unused_plan_credit_usd(plan_id: str, started_at: str, *, now: datetime | None = None) -> int:
    plan = get_plan(plan_id)
    if not plan or plan.get("invite_only") or int(plan.get("price_usd") or 0) <= 0:
        return 0
    raw = (started_at or "").strip()
    if not raw:
        return 0
    try:
        started = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return 0
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    days_used = max(0, (moment - started).days)
    remaining = max(0, BILLING_PERIOD_DAYS - min(BILLING_PERIOD_DAYS, days_used))
    price = int(plan["price_usd"])
    return int(round(price * remaining / BILLING_PERIOD_DAYS))


def quote_plan_change(
    *,
    current_plan: str,
    started_at: str,
    wallet_usd: int,
    new_plan_id: str,
    use_wallet: bool = True,
) -> dict[str, Any]:
    new_plan = get_plan(new_plan_id)
    if not new_plan or new_plan.get("invite_only"):
        raise ValueError("invalid_plan")
    credit = unused_plan_credit_usd(current_plan, started_at)
    price = int(new_plan["price_usd"])
    wallet = max(0, int(wallet_usd or 0))
    due = max(0, price - credit)
    leftover_credit = max(0, credit - price)
    wallet_used = min(wallet, due) if use_wallet else 0
    remainder = max(0, due - wallet_used)
    direction = "same"
    if plan_rank(new_plan_id) > plan_rank(current_plan):
        direction = "upgrade"
    elif plan_rank(new_plan_id) < plan_rank(current_plan):
        direction = "downgrade"
    return {
        "new_plan_id": new_plan["id"],
        "price_usd": price,
        "credit_usd": credit,
        "wallet_usd": wallet,
        "wallet_used_usd": wallet_used,
        "remainder_usd": remainder,
        "leftover_credit_usd": leftover_credit,
        "due_usd": due,
        "instant": remainder == 0,
        "direction": direction,
    }


def get_plan(plan_id: str) -> dict[str, Any] | None:
    pid = (plan_id or "").strip().lower()
    return next((dict(p) for p in PLANS if p["id"] == pid), None)


def get_payment_kind(kind_id: str) -> dict[str, str] | None:
    kid = (kind_id or "").strip().lower()
    return next((dict(k) for k in PAYMENT_KINDS if k["id"] == kid), None)


def plan_rank(plan_id: str) -> int:
    plan = get_plan(plan_id)
    if not plan:
        return -1
    return int(plan["sort"])


def _as_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def parse_iso_utc(raw: str) -> datetime | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _as_utc(dt)


def current_period_start(started_at: str, *, now: datetime | None = None) -> datetime:
    """Inicio del periodo de 30 días vigente para cupos del plan."""
    moment = _as_utc(now or datetime.now(timezone.utc))
    started = parse_iso_utc(started_at)
    if started is None or started > moment:
        return moment
    elapsed = (moment - started).days
    cycles = elapsed // BILLING_PERIOD_DAYS
    return started + timedelta(days=cycles * BILLING_PERIOD_DAYS)
