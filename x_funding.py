"""Config X: una cuenta X paga la API; chequeo diario (4 am) de requisitos para monetizar."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

import db
import publish_schedule

ME_METRICS_URL = "https://api.twitter.com/2/users/me"
CHECK_HOUR_LOCAL = 4  # 4 am hora del panel (UTC-5)
LAST_CHECK_KEY = "x_funding_last_check"
MIN_FOLLOWERS_KEY = "x_monetize_min_followers"
MIN_FOLLOWERS_DEFAULT = 500


def min_followers() -> int:
    raw = (db.get_app_setting(MIN_FOLLOWERS_KEY) or "").strip()
    try:
        val = int(raw)
    except ValueError:
        return MIN_FOLLOWERS_DEFAULT
    return val if val > 0 else MIN_FOLLOWERS_DEFAULT


def set_min_followers(value: int) -> None:
    db.set_app_setting(MIN_FOLLOWERS_KEY, str(max(1, int(value))))


def _fetch_metrics(access_token: str) -> dict[str, Any]:
    params = urllib.parse.urlencode({"user.fields": "username,name,public_metrics"})
    req = urllib.request.Request(
        f"{ME_METRICS_URL}?{params}",
        method="GET",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        detail = ""
        if isinstance(parsed, dict):
            detail = str(parsed.get("detail") or parsed.get("title") or "")
        raise ValueError(detail or raw[:180] or f"HTTP {e.code}") from e
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {}
    user = data.get("data") if isinstance(data.get("data"), dict) else {}
    metrics = user.get("public_metrics") if isinstance(user.get("public_metrics"), dict) else {}
    return {
        "username": str(user.get("username") or "").strip(),
        "followers": int(metrics.get("followers_count") or 0),
        "posts_count": int(metrics.get("tweet_count") or 0),
    }


def check_account(row: dict[str, Any], threshold: int) -> dict[str, Any]:
    """Consulta métricas reales de esa cuenta X y evalúa si ya cumple para monetizar."""
    import x_publish

    oid = str(row.get("id") or "")
    uname = str(row.get("username") or "").strip()
    token = str(row.get("access_token") or "").strip()
    result: dict[str, Any] = {
        "oauth_account_id": oid,
        "username": uname,
        "followers": 0,
        "posts_count": 0,
        "meets": False,
        "detail": "",
        "ok": False,
    }
    if not token:
        result["detail"] = "missing_token"
        return result
    try:
        if x_publish._should_refresh(row):
            try:
                row = x_publish._refresh_row(row)
                token = str(row.get("access_token") or token).strip()
            except ValueError:
                pass
        metrics = _fetch_metrics(token)
    except ValueError as e:
        result["detail"] = str(e)[:200]
        return result
    except Exception as e:
        result["detail"] = str(e)[:200]
        return result
    followers = metrics["followers"]
    meets = followers >= threshold
    result.update(
        {
            "ok": True,
            "username": metrics["username"] or uname,
            "followers": followers,
            "posts_count": metrics["posts_count"],
            "meets": meets,
            "detail": f"{followers}/{threshold}",
        }
    )
    return result


def run_check_now() -> list[dict[str, Any]]:
    """Revisa todas las cuentas X conectadas y guarda el resultado."""
    threshold = min_followers()
    results: list[dict[str, Any]] = []
    for pub in db.list_oauth_accounts_public("x"):
        oid = str(pub.get("id") or "")
        raw = db.get_oauth_account_row(oid)
        if not raw:
            continue
        res = check_account(raw, threshold)
        results.append(res)
        db.save_x_monetize_check(
            oauth_account_id=oid,
            username=res["username"],
            followers=res["followers"],
            posts_count=res["posts_count"],
            meets=res["meets"],
            detail=res["detail"],
        )
    db.set_app_setting(LAST_CHECK_KEY, _today_local())
    return results


def _today_local() -> str:
    return publish_schedule.now_publish_tz().date().isoformat()


def daily_check_due(now_local: datetime | None = None) -> bool:
    """True si ya pasaron las 4 am locales y hoy no se ha hecho el chequeo."""
    now = now_local or publish_schedule.now_publish_tz()
    if now.hour < CHECK_HOUR_LOCAL:
        return False
    last = (db.get_app_setting(LAST_CHECK_KEY) or "").strip()
    return last != now.date().isoformat()


def run_daily_check_if_due() -> bool:
    if not daily_check_due():
        return False
    run_check_now()
    return True
