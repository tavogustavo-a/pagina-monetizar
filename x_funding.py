"""Config X: una cuenta X paga la API; al publicar se revisa seguidores (máx. 1 vez/semana)."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

import db
import publish_schedule

ME_METRICS_URL = "https://api.twitter.com/2/users/me"
LAST_CHECK_KEY = "x_funding_last_check"
MIN_FOLLOWERS_KEY = "x_monetize_min_followers"
MIN_FOLLOWERS_DEFAULT = 500
CHECK_EVERY_DAYS = 7


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
    import proxy_util

    name = str(row.get("account_name") or "").strip()
    proxy_url = proxy_util.active_proxy_url()
    if not proxy_url and name:
        proxy_url = db.get_active_proxy_url_for_account_name(name)
    try:
        def _run():
            local_row = row
            local_token = token
            if x_publish._should_refresh(local_row):
                try:
                    local_row = x_publish._refresh_row(local_row)
                    local_token = str(local_row.get("access_token") or local_token).strip()
                except ValueError:
                    pass
            return _fetch_metrics(local_token)

        with proxy_util.using_proxy(proxy_url):
            metrics = proxy_util.run_slow_retry(_run)
    except ValueError as e:
        result["detail"] = str(e)[:200]
        nice = proxy_util.humanize_network_failure(e, "es")
        if nice:
            result["detail"] = nice
        return result
    except Exception as e:
        nice = proxy_util.humanize_network_failure(e, "es")
        result["detail"] = nice or str(e)[:200]
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


def _parse_checked_at(raw: str) -> datetime | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def check_due_for_oauth(oauth_account_id: str) -> bool:
    oid = (oauth_account_id or "").strip()
    if not oid:
        return False
    row = db.get_x_monetize_check(oid)
    if not row:
        return True
    parsed = _parse_checked_at(str(row.get("checked_at") or ""))
    if not parsed:
        return True
    return datetime.now(timezone.utc) - parsed >= timedelta(days=CHECK_EVERY_DAYS)


def maybe_check_on_publish(account_link_id: str | None) -> None:
    """Si esa cuenta X no se revisó en 7 días, usa esta publicación para consultar seguidores."""
    import proxy_util

    oid = db.resolve_oauth_account_id("x", account_link_id=account_link_id)
    if not oid or not check_due_for_oauth(oid):
        return
    raw = db.get_oauth_account_row(oid)
    if not raw:
        return
    proxy_url = db.get_active_proxy_url_for_account(account_link_id)
    with proxy_util.using_proxy(proxy_url):
        res = check_account(raw, min_followers())
    db.save_x_monetize_check(
        oauth_account_id=oid,
        username=res["username"],
        followers=res["followers"],
        posts_count=res["posts_count"],
        meets=res["meets"],
        detail=res["detail"],
    )


def _today_local() -> str:
    return publish_schedule.now_publish_tz().date().isoformat()
