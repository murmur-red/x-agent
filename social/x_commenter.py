#!/usr/bin/env python3
"""
Light engagement — reply with a short emoji or a few words.

X API on pay-per-use can post/reply but cannot read other users' timelines,
so targets come from comment_targets.json (manual URLs/IDs or auto-queued
after our own calendar posts).

Usage:
  python3 social/x_commenter.py
  python3 social/x_commenter.py --dry-run
  python3 social/x_commenter.py --force
  python3 social/x_commenter.py --add https://x.com/user/status/123456789
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from x_api import credentials_ok, log, post_tweet  # noqa: E402

load_dotenv(ROOT / ".env")

POOL_PATH = Path(__file__).parent / "comment_pool.json"
TARGETS_PATH = Path(__file__).parent / "comment_targets.json"
SEEN_PATH = Path(__file__).parent / "comments_seen.json"
TZ = ZoneInfo(os.getenv("COMMENT_TZ", "Europe/Amsterdam"))
COMMENT_HOUR = int(os.getenv("COMMENT_HOUR", "10"))
MAX_PER_DAY = int(os.getenv("COMMENT_MAX_PER_DAY", "5"))

TWEET_ID_RE = re.compile(r"/status/(\d+)")


def load_json(path: Path, default: dict) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))


def comments_today(seen: dict) -> int:
    today = date.today().isoformat()
    return sum(1 for h in seen.get("history", []) if h.get("date") == today)


def pick_reply(tweet_id: str, pool: list[str]) -> str:
    return random.Random(tweet_id).choice(pool)


def parse_tweet_id(value: str) -> str | None:
    value = value.strip()
    if value.isdigit():
        return value
    match = TWEET_ID_RE.search(value)
    return match.group(1) if match else None


def pending_targets(targets_doc: dict, seen: dict) -> list[dict]:
    done = set(seen.get("commented_tweet_ids", []))
    pending: list[dict] = []
    for item in targets_doc.get("targets", []):
        tid = str(item.get("tweet_id", "")).strip()
        if not tid or tid in done or item.get("status") == "done":
            continue
        pending.append(item)
    return pending


def enqueue_target(
    tweet_id: str,
    *,
    source: str = "manual",
    author: str = "",
    note: str = "",
) -> None:
    doc = load_json(TARGETS_PATH, {"targets": []})
    existing = {str(t.get("tweet_id")) for t in doc.get("targets", [])}
    if tweet_id in existing:
        return
    doc.setdefault("targets", []).append({
        "tweet_id": tweet_id,
        "author": author,
        "source": source,
        "note": note,
        "status": "pending",
        "added": date.today().isoformat(),
    })
    save_json(TARGETS_PATH, doc)


def mark_target_done(targets_doc: dict, tweet_id: str, reply_id: str) -> None:
    for item in targets_doc.get("targets", []):
        if str(item.get("tweet_id")) == tweet_id:
            item["status"] = "done"
            item["reply_tweet_id"] = reply_id
            item["replied"] = datetime.now().isoformat()
            break


def cmd_add(url_or_id: str) -> None:
    tweet_id = parse_tweet_id(url_or_id)
    if not tweet_id:
        print(f"Could not parse tweet id from: {url_or_id}", file=sys.stderr)
        sys.exit(1)
    enqueue_target(tweet_id, source="manual")
    print(f"Queued comment on tweet {tweet_id}")


def run(dry_run: bool = False, force: bool = False) -> int:
    if not credentials_ok():
        log("SKIP | no API keys")
        return 0

    now = datetime.now(TZ)
    if not force and now.hour < COMMENT_HOUR:
        log(f"SKIP | before comment hour {COMMENT_HOUR}:00 {TZ}")
        return 0

    pool_data = load_json(POOL_PATH, {"replies": ["👀", "this", "yep"]})
    pool = [r.strip() for r in pool_data.get("replies", []) if r.strip()]
    if not pool:
        log("SKIP | empty comment pool")
        return 0

    targets_doc = load_json(TARGETS_PATH, {"targets": []})
    seen = load_json(SEEN_PATH, {"commented_tweet_ids": [], "history": []})
    remaining = MAX_PER_DAY - comments_today(seen)
    if remaining <= 0:
        log(f"SKIP | daily cap ({MAX_PER_DAY}) reached")
        return 0

    pending = pending_targets(targets_doc, seen)
    if not pending:
        log("SKIP | no comment targets (add URLs to social/comment_targets.json)")
        return 0

    posted = 0
    for item in pending:
        if posted >= remaining:
            break

        tweet_id = str(item["tweet_id"])
        reply = pick_reply(tweet_id, pool)
        label = item.get("author") or item.get("source") or tweet_id
        log(f"COMMENT | {label} — {reply!r}")
        reply_id = post_tweet(reply, dry_run=dry_run, reply_to=tweet_id)

        if reply_id or dry_run:
            seen.setdefault("commented_tweet_ids", []).append(tweet_id)
            seen.setdefault("history", []).insert(0, {
                "date": date.today().isoformat(),
                "target_tweet_id": tweet_id,
                "target_author": item.get("author", ""),
                "source": item.get("source", ""),
                "reply_text": reply,
                "reply_tweet_id": reply_id or "dry-run",
            })
            seen["commented_tweet_ids"] = seen["commented_tweet_ids"][-500:]
            seen["history"] = seen["history"][:100]
            if not dry_run:
                mark_target_done(targets_doc, tweet_id, reply_id or "")
                save_json(SEEN_PATH, seen)
                save_json(TARGETS_PATH, targets_doc)
            posted += 1

    if dry_run and posted:
        log(f"DRY DONE | would comment on {posted} post(s)")
    elif posted:
        log(f"DONE | commented on {posted} post(s)")
    return posted


def main() -> None:
    parser = argparse.ArgumentParser(description="Short replies on queued X posts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Ignore time-of-day gate")
    parser.add_argument("--add", metavar="URL", help="Queue a tweet URL or ID")
    args = parser.parse_args()

    if args.add:
        cmd_add(args.add)
        return

    run(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()