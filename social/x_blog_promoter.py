#!/usr/bin/env python3
"""
Primary X channel for @murmurRed — 3 posts/week tied to blog articles.

When a new article lands on Monday, Wednesday, or Friday, post one X update:
AI-angled take + link to the article. No calendar spam.

Usage:
  python3 social/x_blog_promoter.py
  python3 social/x_blog_promoter.py --dry-run
  python3 social/x_blog_promoter.py --force          # latest unpromoted (or latest) blog
  python3 social/x_blog_promoter.py --force --id UUID
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from x_api import log, post_tweet  # noqa: E402

load_dotenv(ROOT / ".env")

ARTICLES_URL = os.getenv(
    "ARTICLES_URL",
    "https://raw.githubusercontent.com/murmur-red/murmur/main/articles.json",
)
PROMOTED_PATH = Path(__file__).parent / "promoted.json"
TZ = ZoneInfo(os.getenv("BLOG_PROMO_TZ", "Europe/Amsterdam"))
# Promo days only (Mon=0, Wed=2, Fri=4)
PROMO_WEEKDAYS = {0, 2, 4}
# How long after publish we still try to promote (handles delayed CI)
MAX_AGE_DAYS = int(os.getenv("BLOG_PROMO_MAX_AGE_DAYS", "2"))

TEASER_SYSTEM = """\
You write short X posts for @murmurRed when a new murmur.red blog article goes live.

Voice: human, wry, sharp. Sound like someone who tracks AI and tech in the real world.
Not a press release. Not "excited to announce". Not corporate.

The article may not be about AI on the surface. Your job:
- Lead with an AI / tech / automation / platforms angle that honestly fits the piece
- Bridge smartly from that angle to the article's concrete story (one specific detail)
- Make someone care enough to open the link

Rules:
- Under 200 characters (a full https URL is appended on the next line)
- 1–2 short sentences. Okay to be a little funny or dry.
- No hashtags, no "check out my blog", no "read more", no em dashes
- Do not invent facts that are not in the title/excerpt
- Return ONLY the post text
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


def _parse_date(raw: str) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _is_promo_weekday(d: date) -> bool:
    return d.weekday() in PROMO_WEEKDAYS


def blogs() -> list[dict]:
    out = []
    for a in fetch_articles():
        if a.get("type") != "Blog" or not a.get("url"):
            continue
        d = _parse_date(a.get("date", ""))
        if not d:
            continue
        a = {**a, "_date": d}
        out.append(a)
    out.sort(key=lambda a: a["_date"], reverse=True)
    return out


def candidate_articles(promoted_ids: set[str], force: bool = False) -> list[dict]:
    """Unpromoted blogs published on Mon/Wed/Fri within MAX_AGE_DAYS."""
    today = datetime.now(TZ).date()
    cutoff = today - timedelta(days=MAX_AGE_DAYS)
    candidates = []
    for a in blogs():
        aid = a.get("id", a["url"])
        if aid in promoted_ids and not force:
            continue
        if a["_date"] < cutoff and not force:
            continue
        # Only promote articles that published on a promo weekday
        if not _is_promo_weekday(a["_date"]) and not force:
            continue
        candidates.append(a)
    return candidates


def pick_article(force: bool = False, article_id: str | None = None) -> dict | None:
    promoted = load_promoted()
    promoted_ids = set(promoted.get("promoted_ids", []))

    if article_id:
        for a in blogs():
            if a.get("id") == article_id or a.get("url") == article_id:
                return a
        return None

    if force:
        for a in blogs():
            aid = a.get("id", a["url"])
            if aid not in promoted_ids:
                return a
        return blogs()[0] if blogs() else None

    candidates = candidate_articles(promoted_ids, force=False)
    if not candidates:
        return None

    # Prefer today's article, else most recent unpromoted promo-day post
    today = datetime.now(TZ).date()
    for a in candidates:
        if a["_date"] == today:
            return a
    return candidates[0]


def fetch_blog_excerpt(url: str) -> str:
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True)
        r.raise_for_status()
        text = re.sub(r"<script[^>]*>.*?</script>", " ", r.text, flags=re.I | re.S)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:2000]
    except Exception:
        return ""


def generate_teaser(title: str, topic: str, excerpt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    fallback = (
        f"AI is rewriting how stories like this move. "
        f"New on murmur.red: {title}"
    )[:200]

    if not api_key:
        return fallback

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
    prompt = (
        f"Article title: {title}\n"
        f"Topic tag: {topic or 'tech'}\n\n"
        f"Opening content:\n{excerpt[:1200] or '(no excerpt — use title only)'}"
    )
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=150,
            system=TEASER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip().replace("—", ". ").replace("–", "-")
        text = re.sub(r"\s+", " ", text).strip()
        return text[:200]
    except Exception as e:
        log(f"TEASER | Claude failed — {e}")
        return fallback


def build_post(article: dict) -> str:
    title = article["title"]
    url = article["url"]
    topic = article.get("topic", "")
    excerpt = fetch_blog_excerpt(url)
    teaser = generate_teaser(title, topic, excerpt)
    # Full URL required — costs ~$0.20/tweet on X pay-per-use
    post = f"{teaser}\n\n{url}"
    if len(post) > 280:
        room = 280 - len(url) - 3
        post = f"{teaser[:room].rstrip()}…\n\n{url}"
    return post


def is_promo_day(now: datetime | None = None) -> bool:
    now = now or datetime.now(TZ)
    return now.weekday() in PROMO_WEEKDAYS


def run(dry_run: bool = False, force: bool = False, article_id: str | None = None) -> int:
    now = datetime.now(TZ)

    if not force and not article_id and not is_promo_day(now):
        log(f"SKIP | not a promo day ({now.strftime('%A')}) — only Mon/Wed/Fri")
        return 0

    article = pick_article(force=force, article_id=article_id)
    if not article:
        log("SKIP | no new Mon/Wed/Fri blog article to promote")
        return 0

    article_id = article.get("id", article["url"])
    promoted = load_promoted()
    if article_id in promoted["promoted_ids"] and not force:
        log(f"SKIP | already promoted {article_id}")
        return 0

    post_text = build_post(article)
    log(f"PROMO | {article['title'][:70]}")
    log(f"PROMO | {post_text[:120].replace(chr(10), ' / ')}…")
    tweet_id = post_tweet(post_text, dry_run=dry_run)

    if dry_run:
        return 1

    if tweet_id:
        if article_id not in promoted["promoted_ids"]:
            promoted["promoted_ids"].append(article_id)
        promoted["history"].insert(0, {
            "id": article_id,
            "title": article["title"],
            "url": article["url"],
            "at": datetime.now(timezone.utc).isoformat(),
            "tweet_id": tweet_id,
            "teaser": post_text.split("\n\n")[0][:200],
        })
        promoted["history"] = promoted["history"][:50]
        save_promoted(promoted)
        return 1

    log("FAILED | promo tweet did not post (check X credits / tokens)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote Mon/Wed/Fri blog posts on X")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Ignore weekday/date gates")
    parser.add_argument("--id", dest="article_id", help="Promote specific article id or URL")
    args = parser.parse_args()
    n = run(dry_run=args.dry_run, force=args.force, article_id=args.article_id)
    if n:
        log(f"DONE | promoted {n} post(s)")


if __name__ == "__main__":
    main()
