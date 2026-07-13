#!/usr/bin/env python3
"""
Track estimated X API credit balance and alert when it runs low.

X does not expose dollar balance via API, so we:
  1. Seed balance from X_CREDIT_BALANCE_USD (set when you top up)
  2. Subtract estimated costs from post.log activity each run
  3. Optionally run a daily write probe (CREDIT_DAILY_PROBE=true)
  4. Open a GitHub Issue (emails repo owner) on low balance or 402 errors

Usage:
  python3 social/x_credit_watch.py check
  python3 social/x_credit_watch.py sync-balance 17.24
  python3 social/x_credit_watch.py status
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from x_api import LOG_PATH, credentials_ok, log, verify_connection

STATE_PATH = Path(__file__).parent / "credits_state.json"

COST_POST_TEXT = 0.015
COST_POST_URL = 0.200
COST_READ = 0.010
COST_PROBE = 0.015

DEFAULT_WARN = 5.0
DEFAULT_CRITICAL = 2.0


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "")
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {
        "balance_usd": None,
        "balance_set_at": None,
        "spent_usd": 0.0,
        "log_offset": 0,
        "last_check_at": None,
        "last_probe_at": None,
        "last_probe_ok": True,
        "last_alert_level": None,
        "open_alert_issue": None,
        "events": [],
    }


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _estimate_line_cost(line: str) -> tuple[float, str | None]:
    if "ERROR | 402" in line or "402 Payment Required" in line:
        return 0.0, "exhausted"
    if "POSTED |" in line or "REPLIED |" in line or "LABEL | POSTED" in line:
        if "https://" in line:
            return COST_POST_URL, "post_url"
        return COST_POST_TEXT, "post_text"
    if "get_me" in line.lower():
        return COST_READ, "read"
    return 0.0, None


def ingest_log(state: dict) -> dict:
    if not LOG_PATH.exists():
        return state

    data = LOG_PATH.read_bytes()
    offset = int(state.get("log_offset", 0) or 0)
    if offset > len(data):
        offset = 0

    chunk = data[offset:].decode("utf-8", errors="replace")
    state["log_offset"] = len(data)

    last_signal: str | None = None
    for line in chunk.splitlines():
        cost, kind = _estimate_line_cost(line)
        if kind == "exhausted":
            last_signal = "exhausted"
            state.setdefault("events", []).append({
                "at": datetime.now(timezone.utc).isoformat(),
                "kind": "exhausted",
                "line": line[:200],
            })
            continue
        if cost > 0:
            last_signal = "ok"
            state["spent_usd"] = round(float(state.get("spent_usd", 0)) + cost, 4)
            state.setdefault("events", []).append({
                "at": datetime.now(timezone.utc).isoformat(),
                "kind": kind,
                "cost_usd": cost,
            })

    if last_signal == "exhausted":
        state["_alert_level"] = "exhausted"
    state["events"] = state.get("events", [])[-50:]
    return state


def estimated_balance(state: dict) -> float | None:
    balance = state.get("balance_usd")
    if balance is None:
        return None
    return round(float(balance) - float(state.get("spent_usd", 0)), 2)


def sync_balance(amount: float) -> dict:
    state = load_state()
    state["balance_usd"] = round(amount, 2)
    state["balance_set_at"] = datetime.now(timezone.utc).isoformat()
    state["spent_usd"] = 0.0
    state["log_offset"] = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    state["last_alert_level"] = None
    state["open_alert_issue"] = None
    save_state(state)
    log(f"CREDITS | balance synced to ${amount:.2f}")
    return state


def maybe_apply_env_balance(state: dict) -> dict:
    raw = os.getenv("X_CREDIT_BALANCE_USD", "").strip()
    if not raw:
        return state
    try:
        amount = round(float(raw), 2)
    except ValueError:
        return state
    if state.get("balance_usd") != amount:
        state["balance_usd"] = amount
        state["balance_set_at"] = datetime.now(timezone.utc).isoformat()
        state["spent_usd"] = 0.0
        state["log_offset"] = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
        state["last_alert_level"] = None
        state["open_alert_issue"] = None
        log(f"CREDITS | balance set from env to ${amount:.2f}")
    return state


def daily_probe(state: dict) -> dict:
    if os.getenv("CREDIT_DAILY_PROBE", "true").lower() not in ("1", "true", "yes"):
        return state
    if not credentials_ok():
        return state

    now = datetime.now(timezone.utc)
    probe_hour = int(os.getenv("CREDIT_PROBE_HOUR_UTC", "8"))
    if now.hour != probe_hour:
        return state

    last = state.get("last_probe_at")
    if last and last.startswith(now.date().isoformat()):
        return state

    ok, msg = verify_connection(test_write=True)
    state["last_probe_at"] = now.isoformat()
    state["last_probe_ok"] = ok
    state["spent_usd"] = round(float(state.get("spent_usd", 0)) + COST_PROBE, 4)

    if ok:
        log(f"CREDITS | daily probe OK")
    else:
        log(f"CREDITS | daily probe FAILED — {msg}")
        if "402" in msg or "credits" in msg.lower():
            state["_alert_level"] = "exhausted"

    return state


def _github_request(method: str, url: str, payload: dict | None = None) -> dict | list | None:
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        return None
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        log(f"CREDITS | GitHub API {e.code} — {e.read().decode()[:200]}")
        return None


def _open_github_issue(title: str, body: str) -> int | None:
    repo = os.getenv("GITHUB_REPOSITORY", "murmur-red/x-agent")
    existing = _github_request(
        "GET",
        f"https://api.github.com/repos/{repo}/issues?state=open&labels=credit-alert&per_page=5",
    )
    if isinstance(existing, list) and existing:
        number = existing[0]["number"]
        log(f"CREDITS | alert issue already open — #{number}")
        return number

    created = _github_request(
        "POST",
        f"https://api.github.com/repos/{repo}/issues",
        {"title": title, "body": body, "labels": ["credit-alert", "automation"]},
    )
    if isinstance(created, dict) and created.get("number"):
        number = created["number"]
        log(f"CREDITS | opened alert issue #{number}")
        return number

    # Fallback: gh CLI when running locally
    try:
        out = subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body, "--label", "credit-alert"],
            capture_output=True,
            text=True,
            check=True,
        )
        log(f"CREDITS | {out.stdout.strip()}")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        log(f"CREDITS | could not open GitHub issue — {e}")
    return None


def evaluate_alerts(state: dict) -> str | None:
    forced = state.pop("_alert_level", None)
    remaining = estimated_balance(state)

    # Ignore stale 402 lines if balance still looks healthy.
    if forced == "exhausted" and remaining is not None and remaining > 0:
        forced = None

    if forced:
        return forced
    if remaining is None:
        return None

    critical = _env_float("X_CREDIT_CRITICAL_USD", DEFAULT_CRITICAL)
    warn = _env_float("X_CREDIT_WARN_USD", DEFAULT_WARN)

    if remaining <= 0:
        return "exhausted"
    if remaining <= critical:
        return "critical"
    if remaining <= warn:
        return "warn"
    return None


def send_alert(level: str, state: dict) -> None:
    if state.get("last_alert_level") == level and state.get("open_alert_issue"):
        return

    remaining = estimated_balance(state)
    balance = state.get("balance_usd")
    spent = state.get("spent_usd", 0)

    titles = {
        "warn": "⚠️ X API credits low",
        "critical": "🚨 X API credits critically low",
        "exhausted": "🛑 X API credits exhausted — posting stopped",
    }
    title = titles.get(level, "X API credit alert")

    body = f"""## X API credit alert

**Level:** `{level}`
**Estimated remaining:** `${remaining if remaining is not None else 'unknown'}`
**Seeded balance:** `${balance if balance is not None else 'not set'}`
**Estimated spent since seed:** `${spent:.2f}`
**Checked at:** `{datetime.now(timezone.utc).isoformat()}`

### What to do
1. Open [console.x.com](https://console.x.com) → Billing → **Add credits**
2. Update GitHub secret `X_CREDIT_BALANCE_USD` to your new balance (or run `python3 social/x_credit_watch.py sync-balance <amount>`)
3. Re-run the [X Social Automation](https://github.com/murmur-red/x-agent/actions/workflows/x-social.yml) workflow

Posting costs ~$0.015 per text tweet. Auto top-up at $5 is recommended.

---
*Automated by `social/x_credit_watch.py`*
"""

    issue = _open_github_issue(title, body)
    state["last_alert_level"] = level
    if issue:
        state["open_alert_issue"] = issue
    log(f"CREDITS | ALERT {level} — remaining≈${remaining}")


def check() -> int:
    state = load_state()
    state = maybe_apply_env_balance(state)
    state = ingest_log(state)
    state = daily_probe(state)

    remaining = estimated_balance(state)
    state["last_check_at"] = datetime.now(timezone.utc).isoformat()
    if remaining is not None:
        log(f"CREDITS | estimated remaining ≈ ${remaining:.2f} (spent ${state.get('spent_usd', 0):.2f})")
    else:
        log("CREDITS | balance unknown — set X_CREDIT_BALANCE_USD or run sync-balance")

    level = evaluate_alerts(state)
    if level:
        send_alert(level, state)
        save_state(state)
        return 1 if level == "exhausted" else 0

    if state.get("last_alert_level") and remaining is not None:
        warn = _env_float("X_CREDIT_WARN_USD", DEFAULT_WARN)
        if remaining > warn:
            state["last_alert_level"] = None
            state["open_alert_issue"] = None

    save_state(state)
    return 0


def status() -> None:
    state = load_state()
    remaining = estimated_balance(state)
    print(json.dumps({
        "balance_usd": state.get("balance_usd"),
        "spent_usd": state.get("spent_usd", 0),
        "estimated_remaining_usd": remaining,
        "last_check_at": state.get("last_check_at"),
        "last_probe_ok": state.get("last_probe_ok"),
        "last_alert_level": state.get("last_alert_level"),
        "open_alert_issue": state.get("open_alert_issue"),
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="X API credit monitor")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="Ingest log spend, probe, alert if low")
    sub.add_parser("status", help="Print credit state JSON")
    p_sync = sub.add_parser("sync-balance", help="Reset balance after top-up")
    p_sync.add_argument("amount", type=float)

    args = parser.parse_args()
    if args.cmd == "check":
        sys.exit(check())
    if args.cmd == "status":
        status()
    if args.cmd == "sync-balance":
        sync_balance(args.amount)


if __name__ == "__main__":
    main()