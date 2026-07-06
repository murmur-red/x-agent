#!/usr/bin/env python3
"""
Share new blog posts on @murmurRed — Mon/Wed/Fri ~09:00 Amsterdam time.

The blog agent publishes at 06:00 UTC; this runs at 07:00 UTC (09:00 CEST)
and posts a short teaser + link to today's article.

Usage:
  python3 social/x_blog_promoter.py           # post if today's blog exists
  python3 social/x_blog_promoter.py --dry-run
  python3 social/x_blog_promoter.py --force  # repost latest blog
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from x_api import log, post_tweet  # noqa: E402

load_dotenv(ROOT / ".env")

ARTICLES_URL = "https://raw.githubusercontent.com/murmur-red/murmur/main/articles.json"
PROMOTED_PATH = Path(__file__).parent / "promoted.json"
TZ = ZoneInfo(os.getenv("BLOG_PROMO_TZ", "Europe/Amsterdam"))
PROMO_HOUR = int(os.getenv("BLOG_PROMO_HOUR", "9"))

TEASER_SYSTEM = """\
You write short X posts for @murmurRed promoting a new blog article.

Voice: sharp, curious, AI-aware. Not corporate. No CS jargon.
Rules:
- Under 220 characters (URL will be appended separately)
- Hook with the article's most surprising claim or tension
- No hashtags, no "check out my blog", no em dashes
- One or two short sentences max
- Return ONLY the post text, nothing else
"""


def load_promoted() -> dict:
    if PROMOTED_PATH.exists():
        return json.loads(PROMOTED_PATH.read_text())
    return {"promoted_ids": [], "history": []}


def save_promoted(data: dict) -> None:
    PROMOTED_PATH.write_text(json.dumps(data, indent=2))


def fetch_articles() -> list[dict]:
    r = httpx.get(ARTICLES_URL, timeout=20, follow_redirects=True)
    r.raise_for_status()
    return r.json().get("articles", [])


def latest_blog() -> dict | None:
    for article in fetch_articles():
        if article.get("type") == "Blog" and article.get("url"):
            return article
    return None


def blog_for_today() -> dict | None:
    today = date.today().isoformat()
    blog = latest_blog()
    if blog and blog.get("date", "")[:10] == today:
        return blog
    return None


def fetch_blog_excerpt(url: str) -> str:
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True)
        r.raise_for_status()
        text = re.sub(r"<[^>]+>", " ", r.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1500]
    except Exception:
        return ""


def generate_teaser(title: str, excerpt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return f"New on the blog: {title}"

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
    prompt = f"Article title: {title}\n\nOpening content:\n{excerpt[:800] or '(no excerpt)'}"
    resp = client.messages.create(
        model=model,
        max_tokens=120,
        system=TEASER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip().replace("—", ". ")
    return text[:220]


def build_post(article: dict) -> str:
    title = article["title"]
    url = article["url"]
    excerpt = fetch_blog_excerpt(url)
    teaser = generate_teaser(title, excerpt)
    post = f"{teaser}\n\n{url}"
    if len(post) > 280:
        post = f"{teaser[:200].rstrip()}…\n\n{url}"
    return post


def is_promo_day(now: datetime | None = None) -> bool:
    now = now or datetime.now(TZ)
    return now.weekday() in (0, 2, 4)  # Mon, Wed, Fri


def run(dry_run: bool = False, force: bool = False) -> int:
    now = datetime.now(TZ)
    if not force and not is_promo_day(now):
        log(f"SKIP | not a promo day ({now.strftime('%A')})")
        return 0

    if not force and now.hour < PROMO_HOUR:
        log(f"SKIP | before promo hour {PROMO_HOUR}:00 {TZ}")
        return 0

    article = latest_blog() if force else blog_for_today()
    if not article:
        log("SKIP | no blog post for today")
        return 0

    article_id = article.get("id", article["url"])
    promoted = load_promoted()
    if article_id in promoted["promoted_ids"] and not force:
        log(f"SKIP | already promoted {article_id}")
        return 0

    post_text = build_post(article)
    log(f"PROMO | {article['title'][:60]}")
    tweet_id = post_tweet(post_text, dry_run=dry_run)

    if dry_run:
        return 1

    if tweet_id:
        promoted["promoted_ids"].append(article_id)
        promoted["history"].insert(0, {
            "id": article_id,
            "title": article["title"],
            "url": article["url"],
            "at": datetime.now(timezone.utc).isoformat(),
            "tweet_id": tweet_id,
        })
        save_promoted(promoted)
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote today's blog post on X")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Promote latest blog regardless of date")
    args = parser.parse_args()
    n = run(dry_run=args.dry_run, force=args.force)
    if n:
        log(f"DONE | promoted {n} post(s)")


if __name__ == "__main__":
    main()