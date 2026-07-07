#!/usr/bin/env python3
"""
Engagement replies — short emoji or a few words.

1. Replies to people who mention/comment on @murmurRed (Grok x_search discovery)
2. Replies on contributor posts from follow_list.json (Grok x_search)
3. Manual targets via --add <tweet URL>

Usage:
  python3 social/x_commenter.py
  python3 social/x_commenter.py --dry-run
  python3 social/x_commenter.py --force
  python3 social/x_commenter.py --add https://x.com/user/status/123
  python3 social/x_commenter.py --discover-only
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

from x_api import credentials_ok, engage_tweet, get_client, log  # noqa: E402
from x_discover import discover_contributor_posts, discover_mentions  # noqa: E402

load_dotenv(ROOT / ".env")

FOLLOW_PATH = Path(__file__).parent / "follow_list.json"
OUTBOUND_POOL_PATH = Path(__file__).parent / "comment_pool.json"
MENTION_POOL_PATH = Path(__file__).parent / "mention_reply_pool.json"
TARGETS_PATH = Path(__file__).parent / "comment_targets.json"
SEEN_PATH = Path(__file__).parent / "comments_seen.json"
TZ = ZoneInfo(os.getenv("COMMENT_TZ", "Europe/Amsterdam"))
COMMENT_HOUR = int(os.getenv("COMMENT_HOUR", "10"))
OUTBOUND_MAX = int(os.getenv("COMMENT_MAX_PER_DAY", "5"))
MENTION_MAX = int(os.getenv("MENTION_REPLY_MAX_PER_DAY", "10"))

SOURCE_PRIORITY = {"mention": 0, "contributor": 1, "manual": 2, "own_post": 9}
TWEET_ID_RE = re.compile(r"/status/(\d+)")


def load_json(path: Path, default: dict) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))


def comments_today(seen: dict, source: str | None = None) -> int:
    today = date.today().isoformat()
    items = seen.get("history", [])
    if source is None:
        return sum(1 for h in items if h.get("date") == today)
    return sum(1 for h in items if h.get("date") == today and h.get("source") == source)


def pick_reply(tweet_id: str, pool: list[str]) -> str:
    return random.Random(tweet_id).choice(pool)


def parse_tweet_id(value: str) -> str | None:
    value = value.strip()
    if value.isdigit():
        return value
    match = TWEET_ID_RE.search(value)
    return match.group(1) if match else None


def follow_handles() -> list[str]:
    follow = load_json(FOLLOW_PATH, {"accounts": []})
    return [
        a["handle"].lstrip("@")
        for a in follow.get("accounts", [])
        if a.get("handle")
    ]


def enqueue_target(
    tweet_id: str,
    *,
    source: str = "manual",
    author: str = "",
    note: str = "",
) -> bool:
    doc = load_json(TARGETS_PATH, {"targets": []})
    existing = {
        str(t.get("tweet_id"))
        for t in doc.get("targets", [])
        if t.get("status") != "done"
    }
    if tweet_id in existing:
        return False
    doc.setdefault("targets", []).append({
        "tweet_id": tweet_id,
        "author": author,
        "source": source,
        "note": note,
        "status": "pending",
        "added": date.today().isoformat(),
    })
    save_json(TARGETS_PATH, doc)
    return True


def mark_target_done(targets_doc: dict, tweet_id: str, reply_id: str) -> None:
    for item in targets_doc.get("targets", []):
        if str(item.get("tweet_id")) == tweet_id:
            item["status"] = "done"
            item["reply_tweet_id"] = reply_id
            item["replied"] = datetime.now().isoformat()
            break


def pending_targets(targets_doc: dict, seen: dict) -> list[dict]:
    done = set(seen.get("commented_tweet_ids", []))
    pending: list[dict] = []
    for item in targets_doc.get("targets", []):
        tid = str(item.get("tweet_id", "")).strip()
        if not tid or tid in done or item.get("status") == "done":
            continue
        pending.append(item)
    pending.sort(key=lambda x: SOURCE_PRIORITY.get(x.get("source", ""), 8))
    return pending


def discover_and_enqueue(seen: dict) -> tuple[int, int]:
    """Scan mentions + contributors; return (mentions_queued, contributors_queued)."""
    my_handle = "murmurRed"
    try:
        me = get_client().get_me()
        if me.data:
            my_handle = me.data.username
    except Exception:
        pass

    done = set(seen.get("commented_tweet_ids", []))
    m_queued = 0
    c_queued = 0

    mention_slots = max(0, MENTION_MAX - comments_today(seen, "mention"))
    if mention_slots:
        for post in discover_mentions(my_handle, max_posts=mention_slots):
            if post["tweet_id"] in done:
                continue
            if post["author"].lower() == my_handle.lower():
                continue
            if enqueue_target(
                post["tweet_id"],
                source="mention",
                author=post["author"],
                note=post.get("text", ""),
            ):
                m_queued += 1

    outbound_slots = max(0, OUTBOUND_MAX - comments_today(seen, "contributor"))
    if outbound_slots:
        handles = follow_handles()
        for post in discover_contributor_posts(handles, max_posts=outbound_slots):
            if post["tweet_id"] in done:
                continue
            if post["author"].lower() == my_handle.lower():
                continue
            if enqueue_target(
                post["tweet_id"],
                source="contributor",
                author=post["author"],
                note=post.get("text", ""),
            ):
                c_queued += 1

    if m_queued or c_queued:
        log(f"DISCOVER | queued {m_queued} mention(s), {c_queued} contributor(s)")
    return m_queued, c_queued


def pool_for_source(source: str, outbound: list[str], mention: list[str]) -> list[str]:
    if source == "mention":
        return mention or outbound
    return outbound or mention


def run(dry_run: bool = False, force: bool = False, discover_only: bool = False) -> int:
    if not credentials_ok():
        log("SKIP | no API keys")
        return 0

    now = datetime.now(TZ)
    if not force and now.hour < COMMENT_HOUR:
        log(f"SKIP | before comment hour {COMMENT_HOUR}:00 {TZ}")
        return 0

    outbound_pool = [
        r.strip()
        for r in load_json(OUTBOUND_POOL_PATH, {"replies": []}).get("replies", [])
        if r.strip()
    ]
    mention_pool = [
        r.strip()
        for r in load_json(MENTION_POOL_PATH, {"replies": []}).get("replies", [])
        if r.strip()
    ]
    if not outbound_pool and not mention_pool:
        log("SKIP | empty reply pools")
        return 0

    seen = load_json(SEEN_PATH, {"commented_tweet_ids": [], "history": []})
    discover_and_enqueue(seen)
    if discover_only:
        return 0

    targets_doc = load_json(TARGETS_PATH, {"targets": []})
    pending = pending_targets(targets_doc, seen)
    if not pending:
        log("SKIP | no comment targets after discovery")
        return 0

    posted = 0
    for item in pending:
        source = item.get("source", "manual")
        if source == "mention" and comments_today(seen, "mention") >= MENTION_MAX:
            continue
        if source == "contributor" and comments_today(seen, "contributor") >= OUTBOUND_MAX:
            continue
        if source not in ("mention", "contributor") and comments_today(seen) >= OUTBOUND_MAX + MENTION_MAX:
            continue

        pool = pool_for_source(source, outbound_pool, mention_pool)
        tweet_id = str(item["tweet_id"])
        reply = pick_reply(tweet_id, pool)
        label = f"@{item['author']}" if item.get("author") else source
        mode = "reply" if source == "mention" else "mention_tweet"
        log(f"COMMENT | {label} ({source}/{mode}) — {reply!r}")
        if source == "mention":
            reply_id = engage_tweet(reply, reply_to=tweet_id, dry_run=dry_run)
        else:
            # X blocks cold thread replies — @mention as a standalone post instead
            reply_id = engage_tweet(
                reply,
                mention_author=item.get("author", ""),
                dry_run=dry_run,
            )

        if reply_id or dry_run:
            seen.setdefault("commented_tweet_ids", []).append(tweet_id)
            seen.setdefault("history", []).insert(0, {
                "date": date.today().isoformat(),
                "target_tweet_id": tweet_id,
                "target_author": item.get("author", ""),
                "source": source,
                "reply_text": reply,
                "engage_mode": mode,
                "reply_tweet_id": reply_id or "dry-run",
            })
            seen["commented_tweet_ids"] = seen["commented_tweet_ids"][-500:]
            seen["history"] = seen["history"][:200]
            if not dry_run:
                mark_target_done(targets_doc, tweet_id, reply_id or "")
                save_json(SEEN_PATH, seen)
                save_json(TARGETS_PATH, targets_doc)
            posted += 1

    if dry_run and posted:
        log(f"DRY DONE | would comment on {posted} post(s)")
    elif posted:
        save_json(SEEN_PATH, seen)
        save_json(TARGETS_PATH, targets_doc)
        log(f"DONE | commented on {posted} post(s)")
    return posted


def cmd_add(url_or_id: str) -> None:
    tweet_id = parse_tweet_id(url_or_id)
    if not tweet_id:
        print(f"Could not parse tweet id from: {url_or_id}", file=sys.stderr)
        sys.exit(1)
    enqueue_target(tweet_id, source="manual")
    print(f"Queued comment on tweet {tweet_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reply on contributor posts and mentions")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Ignore time-of-day gate")
    parser.add_argument("--discover-only", action="store_true", help="Scan only, do not post")
    parser.add_argument("--add", metavar="URL", help="Queue a tweet URL or ID")
    args = parser.parse_args()

    if args.add:
        cmd_add(args.add)
        return

    run(dry_run=args.dry_run, force=args.force, discover_only=args.discover_only)


if __name__ == "__main__":
    main()