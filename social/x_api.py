"""Shared X API helpers for all murmur.red social automation."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent / "post.log"


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} | {msg}"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")
    print(line)


def credentials_ok() -> bool:
    keys = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
    return all(os.getenv(k, "") for k in keys)


def get_client():
    import tweepy

    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def post_tweet(text: str, dry_run: bool = False) -> str | None:
    if len(text) > 280:
        text = text[:277] + "..."

    if dry_run or not credentials_ok():
        log(f"DRY | {text}")
        return None

    try:
        resp = get_client().create_tweet(text=text)
        tweet_id = str(resp.data["id"])
        log(f"POSTED | https://x.com/i/web/status/{tweet_id}")
        return tweet_id
    except Exception as e:
        log(f"ERROR | {e}")
        return None