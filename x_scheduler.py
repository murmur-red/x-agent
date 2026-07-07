#!/usr/bin/env python3
"""
murmur.red X scheduler — fully automatic posting once API keys are set.

One-time setup (only manual step after creating your X account):
  python3 x_scheduler.py init          # paste 4 API keys → validates → writes .env
  bash social/install_autopost.sh      # installs background daemon (macOS launchd)

Then forget about it. The daemon checks every 10 min and posts due content.

Other commands:
  python3 x_scheduler.py status        # verify API keys work
  python3 x_scheduler.py today         # preview today's queue
  python3 x_scheduler.py dry-run       # preview due posts without posting
  python3 x_scheduler.py uninstall     # stop background daemon
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
SOCIAL_DIR = ROOT / "social"
CALENDAR_PATH = SOCIAL_DIR / "content_calendar.csv"
POSTED_PATH = SOCIAL_DIR / "posted.json"
LOG_PATH = SOCIAL_DIR / "post.log"
ENV_PATH = ROOT / ".env"
PLIST_LABEL = "com.murmur.red.xscheduler"

sys.path.insert(0, str(SOCIAL_DIR))
from x_content import ACCOUNT_SETUP_STEPS, BRAND  # noqa: E402

THREAD_DELAY_SEC = 5
TWEET_DELAY_SEC = 2


@dataclass
class CalendarRow:
    index: int
    date: str
    time_utc: str
    week: str
    content_type: str
    thread_id: str
    thread_part: str
    post_text: str
    media_note: str
    status: str

    @property
    def scheduled_at(self) -> datetime:
        return datetime.fromisoformat(f"{self.date}T{self.time_utc}:00").replace(tzinfo=timezone.utc)

    @property
    def row_id(self) -> str:
        return f"{self.date}_{self.time_utc}_{self.thread_id or 'single'}_{self.thread_part}"


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} | {msg}"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")
    print(line)


def load_calendar() -> list[CalendarRow]:
    if not CALENDAR_PATH.exists():
        from build_calendar import main as build
        build()
    rows: list[CalendarRow] = []
    with CALENDAR_PATH.open(encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            rows.append(CalendarRow(index=i, **row))
    return rows


def load_posted() -> dict:
    if POSTED_PATH.exists():
        return json.loads(POSTED_PATH.read_text())
    return {"posted_ids": [], "tweet_ids": {}}


def save_posted(data: dict) -> None:
    POSTED_PATH.write_text(json.dumps(data, indent=2))


def due_now(rows: list[CalendarRow], now: datetime | None = None) -> list[CalendarRow]:
    now = now or datetime.now(timezone.utc)
    posted = set(load_posted()["posted_ids"])
    due: list[CalendarRow] = []
    for row in rows:
        if row.status != "scheduled" or row.row_id in posted:
            continue
        if row.scheduled_at <= now:
            due.append(row)
    due.sort(key=lambda r: (r.scheduled_at, int(r.thread_part or 0)))
    return due


def group_into_batches(due: list[CalendarRow]) -> list[list[CalendarRow]]:
    """Thread parts stay together; singles are individual batches."""
    thread_groups: dict[tuple[str, str], list[CalendarRow]] = {}
    singles: list[list[CalendarRow]] = []

    for row in due:
        if row.thread_id:
            key = (row.date, row.thread_id)
            thread_groups.setdefault(key, []).append(row)
        else:
            singles.append([row])

    batches: list[list[CalendarRow]] = []
    for parts in thread_groups.values():
        batches.append(sorted(parts, key=lambda r: int(r.thread_part or 0)))
    batches.extend(singles)
    batches.sort(key=lambda b: (b[0].scheduled_at, int(b[0].thread_part or 0)))
    return batches


def _credentials() -> dict[str, str]:
    return {
        "api_key": os.getenv("X_API_KEY", ""),
        "api_secret": os.getenv("X_API_SECRET", ""),
        "access_token": os.getenv("X_ACCESS_TOKEN", ""),
        "access_secret": os.getenv("X_ACCESS_TOKEN_SECRET", ""),
    }


def credentials_ok() -> bool:
    return all(_credentials().values())


def _get_x_client():
    import tweepy

    creds = _credentials()
    if not all(creds.values()):
        return None
    return tweepy.Client(
        consumer_key=creds["api_key"],
        consumer_secret=creds["api_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_secret"],
    )


def verify_api(test_write: bool = False) -> bool:
    from x_api import verify_connection

    ok, msg = verify_connection(test_write=test_write)
    prefix = "✅" if ok else "❌"
    print(f"{prefix} {msg}")
    return ok


def post_tweet(text: str, reply_to: str | None = None) -> str | None:
    client = _get_x_client()
    if client is None:
        log(f"DRY | {text[:80]}...")
        return None

    kwargs: dict = {"text": text[:280]}
    if reply_to:
        kwargs["in_reply_to_tweet_id"] = reply_to

    try:
        resp = client.create_tweet(**kwargs)
        tweet_id = str(resp.data["id"])
        log(f"POSTED | https://x.com/i/web/status/{tweet_id}")
        return tweet_id
    except Exception as e:
        log(f"ERROR | {e}")
        return None


def _queue_self_reply(tweet_id: str, row: CalendarRow) -> None:
    """Queue a short follow-up reply under our own post (optional)."""
    if os.getenv("COMMENT_SELF_REPLY", "false").lower() not in ("1", "true", "yes"):
        return
    if row.thread_id and int(row.thread_part or 0) > 1:
        return
    try:
        from x_commenter import enqueue_target

        enqueue_target(tweet_id, source="own_post", note=row.row_id)
    except Exception as exc:
        log(f"COMMENT QUEUE | skip — {exc}")


def execute_post(rows: list[CalendarRow], force_index: int | None = None) -> int:
    if not credentials_ok():
        log("SKIP | no API keys — run: python3 x_scheduler.py init")
        return 0

    posted_data = load_posted()
    posted_ids = set(posted_data["posted_ids"])
    tweet_ids: dict[str, str] = posted_data.get("tweet_ids", {})

    if force_index is not None:
        targets = [r for r in rows if r.index == force_index]
        batches = [[t] for t in targets]
    else:
        due = [r for r in due_now(rows) if r.row_id not in posted_ids]
        if not due:
            return 0
        batches = group_into_batches(due)

    count = 0
    for batch in batches:
        reply_to: str | None = None
        for i, row in enumerate(batch):
            if row.row_id in posted_ids:
                if row.thread_id:
                    prev_key = f"{row.date}_{row.thread_id}_{row.thread_part}"
                    reply_to = tweet_ids.get(prev_key)
                continue

            if row.thread_id and int(row.thread_part or 0) > 1:
                prev_key = f"{row.date}_{row.thread_id}_{int(row.thread_part) - 1}"
                reply_to = tweet_ids.get(prev_key)
                if not reply_to:
                    log(f"SKIP | thread part {row.thread_part} — previous part missing")
                    break

            tweet_id = post_tweet(row.post_text, reply_to=reply_to)
            posted_ids.add(row.row_id)

            if tweet_id:
                if row.thread_id:
                    key = f"{row.date}_{row.thread_id}_{row.thread_part}"
                    tweet_ids[key] = tweet_id
                    reply_to = tweet_id
                else:
                    tweet_ids[row.row_id] = tweet_id
                _queue_self_reply(tweet_id, row)
                count += 1
            elif not credentials_ok():
                break
            else:
                log(f"FAILED | {row.row_id}")
                if row.thread_id:
                    break

            if i < len(batch) - 1:
                time.sleep(THREAD_DELAY_SEC if row.thread_id else TWEET_DELAY_SEC)

        save_posted({"posted_ids": list(posted_ids), "tweet_ids": tweet_ids})
        if len(batch) > 1 or (batch and not batch[0].thread_id):
            time.sleep(TWEET_DELAY_SEC)

    return count


def _upsert_env(updates: dict[str, str]) -> None:
    lines: list[str] = []
    seen = set()
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            key = line.split("=", 1)[0] if "=" in line and not line.startswith("#") else ""
            if key in updates:
                lines.append(f"{key}={updates[key]}")
                seen.add(key)
            else:
                lines.append(line)
    for key, val in updates.items():
        if key not in seen:
            lines.append(f"{key}={val}")
    ENV_PATH.write_text("\n".join(lines) + "\n")


def cmd_init() -> None:
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  murmur.red X — one-time autopost setup                     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("Prerequisites (one-time, on developer.x.com):")
    print("  1. Create a Project + App at https://developer.x.com")
    print("  2. User authentication → OAuth 1.0a → Read and Write")
    print("  3. Generate Access Token & Secret (must be for YOUR account)")
    print()

    keys = {
        "X_API_KEY": "API Key (Consumer Key)",
        "X_API_SECRET": "API Key Secret (Consumer Secret)",
        "X_ACCESS_TOKEN": "Access Token",
        "X_ACCESS_TOKEN_SECRET": "Access Token Secret",
    }
    updates: dict[str, str] = {}
    for env_key, label in keys.items():
        existing = os.getenv(env_key, "")
        if existing and env_key not in updates:
            prompt = f"{label} [{existing[:6]}…]: "
        else:
            prompt = f"{label}: "
        val = input(prompt).strip()
        updates[env_key] = val or existing

    if not all(updates.values()):
        print("❌ All 4 keys are required.")
        sys.exit(1)

    _upsert_env(updates)
    load_dotenv(override=True)

    if not verify_api():
        sys.exit(1)

    from build_calendar import main as build
    build()

    print()
    print("✅ Keys saved to .env and verified.")
    print()
    print("Next (installs background daemon — posts automatically every 10 min):")
    print(f"  bash {SOCIAL_DIR}/install_autopost.sh")
    print()
    print(f"Brand bio for your profile:\n{BRAND['bio']}")


def cmd_uninstall() -> None:
    uid = os.getuid()
    target = f"gui/{uid}/{PLIST_LABEL}"
    subprocess.run(["launchctl", "bootout", target], capture_output=True)
    plist = Path.home() / "Library/LaunchAgents" / f"{PLIST_LABEL}.plist"
    if plist.exists():
        plist.unlink()
    print(f"✅ Stopped and removed {PLIST_LABEL}")


def cmd_setup() -> None:
    print(ACCOUNT_SETUP_STEPS)
    print(f"\nBrand bio:\n{BRAND['bio']}\n")
    print("Autopost setup:")
    print("  python3 x_scheduler.py init")
    print("  bash social/install_autopost.sh")


def cmd_today(rows: list[CalendarRow]) -> None:
    today = date.today().isoformat()
    today_rows = [r for r in rows if r.date == today]
    if not today_rows:
        print(f"No posts scheduled for {today}.")
        return
    for r in today_rows:
        print(f"\n⏰ {r.time_utc} UTC | {r.content_type} | week {r.week}")
        if r.media_note:
            print(f"   📎 {r.media_note}")
        print(f"   {r.post_text[:120]}...")


def cmd_week(rows: list[CalendarRow]) -> None:
    today = date.today()
    end = today.toordinal() + 7
    week_rows = [r for r in rows if today.toordinal() <= date.fromisoformat(r.date).toordinal() < end]
    print(f"📅 {len(week_rows)} posts in the next 7 days\n")
    for r in week_rows:
        print(f"  {r.date} {r.time_utc} | w{r.week} | {r.content_type:8} | {r.post_text[:60]}...")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="murmur.red X autopost scheduler")
    parser.add_argument(
        "command",
        choices=["init", "setup", "status", "calendar", "today", "week", "dry-run", "post", "uninstall"],
    )
    parser.add_argument("--force", type=int, default=None, help="Post calendar row by index")
    parser.add_argument("--write-test", action="store_true", help="Also test create_tweet permission")
    args = parser.parse_args()

    if args.command == "init":
        load_dotenv(override=True)
        cmd_init()
        return

    if args.command == "setup":
        cmd_setup()
        return

    if args.command == "status":
        sys.exit(0 if verify_api(test_write=args.write_test) else 1)

    if args.command == "uninstall":
        cmd_uninstall()
        return

    if args.command == "calendar":
        from build_calendar import main as build
        build()
        return

    rows = load_calendar()

    if args.command == "today":
        cmd_today(rows)
    elif args.command == "week":
        cmd_week(rows)
    elif args.command == "dry-run":
        due = due_now(rows) if args.force is None else [r for r in rows if r.index == args.force]
        print(f"{'Forced' if args.force is not None else 'Due'}: {len(due)} post(s)\n")
        for r in due:
            print(f"─── [{r.index}] {r.date} {r.time_utc} | {r.content_type} ───")
            print(r.post_text)
            if r.media_note:
                print(f"📎 {r.media_note}")
            print()
    elif args.command == "post":
        n = execute_post(rows, force_index=args.force)
        if n:
            log(f"BATCH | posted {n} tweet(s)")


if __name__ == "__main__":
    main()