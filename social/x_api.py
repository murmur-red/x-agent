"""Shared X API helpers for all murmur.red social automation."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent / "post.log"

WRITE_PERMISSION_HINT = (
    "X token is read-only. developer.x.com → your app → Read and Write → "
    "regenerate Access Token & Secret → update GitHub secrets + .env"
)

PAYMENT_REQUIRED_HINT = (
    "X API credits exhausted. console.x.com → purchase credits "
    "(~$0.015/text tweet, ~$0.20/tweet with https URL)"
)


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


def _is_write_permission_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    if "duplicate content" in msg:
        return False
    return "403" in msg or "oauth1 app permissions" in msg or "not permitted" in msg


def _is_payment_required_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "402" in msg or "payment required" in msg or "does not have any credits" in msg


def verify_connection(test_write: bool = False) -> tuple[bool, str]:
    """Return (ok, message). get_me always; optional write probe with --write-test."""
    if not credentials_ok():
        return False, "Missing X API keys"

    try:
        client = get_client()
        me = client.get_me()
        if not me.data:
            return False, "get_me returned no user"
        username = me.data.username
    except Exception as e:
        return False, f"Read check failed: {e}"

    if not test_write:
        return True, (
            f"@{username} read OK (post permission not tested — "
            f"run: python3 x_scheduler.py status --write-test)"
        )

    try:
        probe = f"ping {datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        client.create_tweet(text=probe)
    except Exception as e:
        if _is_write_permission_error(e):
            return False, f"@{username} cannot post. {WRITE_PERMISSION_HINT}"
        if _is_payment_required_error(e):
            return False, f"@{username} cannot post. {PAYMENT_REQUIRED_HINT}"
        return False, f"Write check failed: {e}"

    return True, f"@{username} read+write OK"


def engage_tweet(
    text: str,
    *,
    reply_to: str | None = None,
    mention_author: str = "",
    dry_run: bool = False,
) -> str | None:
    """Reply in-thread, or @mention standalone when X blocks cold replies."""
    if mention_author and not reply_to:
        handle = mention_author.lstrip("@")
        text = f"@{handle} {text}"
    return post_tweet(text, dry_run=dry_run, reply_to=reply_to)


def post_tweet(
    text: str,
    dry_run: bool = False,
    *,
    reply_to: str | None = None,
) -> str | None:
    if len(text) > 280:
        text = text[:277] + "..."

    if dry_run or not credentials_ok():
        prefix = f"REPLY@{reply_to} | " if reply_to else ""
        log(f"DRY | {prefix}{text}")
        return None

    try:
        kwargs: dict = {"text": text}
        if reply_to:
            kwargs["in_reply_to_tweet_id"] = reply_to
        resp = get_client().create_tweet(**kwargs)
        tweet_id = str(resp.data["id"])
        label = "REPLIED" if reply_to else "POSTED"
        log(f"{label} | https://x.com/i/web/status/{tweet_id}")
        return tweet_id
    except Exception as e:
        if _is_write_permission_error(e):
            log(f"ERROR | 403 write forbidden — {WRITE_PERMISSION_HINT}")
        elif _is_payment_required_error(e):
            log(f"ERROR | 402 no credits — {PAYMENT_REQUIRED_HINT}")
        else:
            log(f"ERROR | {e}")
        return None