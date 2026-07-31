#!/usr/bin/env python3
"""
Primary X channel for @murmurRed — promote new blog.murmur.red posts.

When a new article lands on Monday, Wednesday, or Friday, post one short
X update + full article link. Text only (no images / media uploads).

Usage:
  python3 social/x_blog_promoter.py
  python3 social/x_blog_promoter.py --dry-run
  python3 social/x_blog_promoter.py --force          # latest unpromoted (or latest) blog
  python3 social/x_blog_promoter.py --force --id URL
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from x_api import log, post_tweet  # noqa: E402

load_dotenv(ROOT / ".env")

# Live blog is the source of truth (Atom feed). articles.json is fallback only.
BLOG_FEED_URL = os.getenv("BLOG_FEED_URL", "https://blog.murmur.red/feed.xml")
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

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}

TEASER_SYSTEM = """\
You write short X posts for @murmurRed when a new blog.murmur.red article goes live.

Voice: human, wry, sharp. Sound like someone who tracks AI and tech in the real world.
Not a press release. Not "excited to announce". Not corporate.

Rules:
- Under 200 characters (a full https URL is appended on the next line)
- 1–2 short sentences. Okay to be a little funny or dry.
- No hashtags, no "check out my blog", no "read more", no em dashes
- Do not invent facts that are not in the title/summary
- No image or media description — plain text only
- Return ONLY the post text
"""


def load_promoted() -> dict:
    if PROMOTED_PATH.exists():
        return json.loads(PROMOTED_PATH.read_text())
    return {"promoted_ids": [], "history": []}


def save_promoted(data: dict) -> None:
    PROMOTED_PATH.write_text(json.dumps(data, indent=2) + "\n")


def _parse_date(raw: str) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _is_promo_weekday(d: date) -> bool:
    return d.weekday() in PROMO_WEEKDAYS


def _normalize_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return (el.text or "").strip()


def _strip_html(raw: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_from_feed() -> list[dict]:
    """Scan blog.murmur.red Atom feed (primary source)."""
    r = httpx.get(BLOG_FEED_URL, timeout=20, follow_redirects=True)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    out: list[dict] = []
    for entry in root.findall("a:entry", ATOM_NS):
        title = _text(entry.find("a:title", ATOM_NS))
        link_el = entry.find("a:link", ATOM_NS)
        url = ""
        if link_el is not None:
            url = link_el.get("href", "") or ""
        if not url:
            # Some feeds put link as child text
            for link in entry.findall("a:link", ATOM_NS):
                if link.get("rel") in (None, "alternate") and link.get("href"):
                    url = link.get("href", "")
                    break
        published = _text(entry.find("a:published", ATOM_NS)) or _text(
            entry.find("a:updated", ATOM_NS)
        )
        entry_id = _text(entry.find("a:id", ATOM_NS)) or url
        summary = _text(entry.find("a:summary", ATOM_NS))
        if not summary:
            content = entry.find("a:content", ATOM_NS)
            summary = _strip_html(_text(content))[:500] if content is not None else ""
        else:
            summary = _strip_html(summary)
        d = _parse_date(published)
        if not title or not url or not d:
            continue
        out.append(
            {
                "id": entry_id,
                "title": title,
                "url": url,
                "date": d.isoformat(),
                "_date": d,
                "topic": "tech",
                "summary": summary,
                "source": "feed",
            }
        )
    out.sort(key=lambda a: a["_date"], reverse=True)
    return out


def fetch_from_articles_json() -> list[dict]:
    """Fallback index if the live feed is unreachable."""
    r = httpx.get(ARTICLES_URL, timeout=20, follow_redirects=True)
    r.raise_for_status()
    out: list[dict] = []
    for a in r.json().get("articles", []):
        if a.get("type") != "Blog" or not a.get("url"):
            continue
        d = _parse_date(a.get("date", ""))
        if not d:
            continue
        out.append(
            {
                **a,
                "_date": d,
                "summary": a.get("summary", ""),
                "source": "articles_json",
            }
        )
    out.sort(key=lambda a: a["_date"], reverse=True)
    return out


def blogs() -> list[dict]:
    try:
        items = fetch_from_feed()
        if items:
            return items
    except Exception as e:
        log(f"FEED | blog.murmur.red feed failed — {e}; falling back to articles.json")
    return fetch_from_articles_json()


def already_promoted(article: dict, promoted: dict) -> bool:
    ids = set(promoted.get("promoted_ids", []))
    urls = {_normalize_url(h.get("url", "")) for h in promoted.get("history", [])}
    aid = article.get("id", "")
    url = _normalize_url(article.get("url", ""))
    if aid and aid in ids:
        return True
    if url and url in urls:
        return True
    # UUID vs feed-id: match on path suffix
    path = url.rsplit("/", 1)[-1] if url else ""
    if path:
        for h in promoted.get("history", []):
            if _normalize_url(h.get("url", "")).endswith(path):
                return True
    return False


def candidate_articles(promoted: dict, force: bool = False) -> list[dict]:
    """Unpromoted blogs published on Mon/Wed/Fri within MAX_AGE_DAYS."""
    today = datetime.now(TZ).date()
    cutoff = today - timedelta(days=MAX_AGE_DAYS)
    candidates = []
    for a in blogs():
        if already_promoted(a, promoted) and not force:
            continue
        if a["_date"] < cutoff and not force:
            continue
        if not _is_promo_weekday(a["_date"]) and not force:
            continue
        candidates.append(a)
    return candidates


def pick_article(force: bool = False, article_id: str | None = None) -> dict | None:
    promoted = load_promoted()

    if article_id:
        needle = article_id.strip()
        for a in blogs():
            if (
                a.get("id") == needle
                or a.get("url") == needle
                or _normalize_url(a.get("url", "")) == _normalize_url(needle)
            ):
                return a
        return None

    if force:
        for a in blogs():
            if not already_promoted(a, promoted):
                return a
        return blogs()[0] if blogs() else None

    candidates = candidate_articles(promoted, force=False)
    if not candidates:
        return None

    today = datetime.now(TZ).date()
    for a in candidates:
        if a["_date"] == today:
            return a
    return candidates[0]


def fetch_blog_excerpt(url: str) -> str:
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True)
        r.raise_for_status()
        return _strip_html(r.text)[:2000]
    except Exception:
        return ""


def _clean_teaser(text: str) -> str:
    text = text.strip().replace("—", ". ").replace("–", "-")
    text = re.sub(r"\s+", " ", text).strip()
    # Strip accidental surrounding quotes from models
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text[:200]


def generate_teaser(title: str, topic: str, excerpt: str) -> str:
    """Short plain-text teaser. Prefers Claude, then Grok, then title-based fallback."""
    prompt = (
        f"Article title: {title}\n"
        f"Topic tag: {topic or 'tech'}\n\n"
        f"Opening content:\n{excerpt[:1200] or '(no excerpt — use title only)'}"
    )

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)
            model = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
            resp = client.messages.create(
                model=model,
                max_tokens=150,
                system=TEASER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            return _clean_teaser(resp.content[0].text)
        except Exception as e:
            log(f"TEASER | Claude failed — {e}")

    xai_key = os.getenv("XAI_API_KEY", "")
    if xai_key:
        try:
            r = httpx.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {xai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.getenv("XAI_MODEL", "grok-3"),
                    "messages": [
                        {"role": "system", "content": TEASER_SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 150,
                },
                timeout=30,
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            return _clean_teaser(text)
        except Exception as e:
            log(f"TEASER | Grok failed — {e}")

    # Plain fallback — still a short tweet, not corporate
    short = title.rstrip(".")
    if len(short) > 160:
        short = short[:157].rstrip() + "…"
    return short


def build_post(article: dict) -> str:
    """Plain text + URL only. No media, no cards we control — just the tweet body."""
    title = article["title"]
    url = article["url"]
    topic = article.get("topic", "")
    excerpt = article.get("summary") or fetch_blog_excerpt(url)
    teaser = generate_teaser(title, topic, excerpt)
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

    promoted = load_promoted()
    if already_promoted(article, promoted) and not force:
        log(f"SKIP | already promoted {article.get('id', article['url'])}")
        return 0

    post_text = build_post(article)
    log(f"PROMO | {article['title'][:70]}")
    log(f"PROMO | {post_text[:120].replace(chr(10), ' / ')}…")
    # Text-only post: post_tweet never attaches media
    tweet_id = post_tweet(post_text, dry_run=dry_run)

    if dry_run:
        return 1

    if tweet_id:
        store_id = article.get("id") or article["url"]
        if store_id not in promoted["promoted_ids"]:
            promoted["promoted_ids"].append(store_id)
        # Also store URL for cross-source dedup (feed id vs articles.json uuid)
        url = _normalize_url(article["url"])
        if url and url not in promoted["promoted_ids"]:
            promoted["promoted_ids"].append(url)
        promoted["history"].insert(
            0,
            {
                "id": store_id,
                "title": article["title"],
                "url": article["url"],
                "at": datetime.now(timezone.utc).isoformat(),
                "tweet_id": tweet_id,
                "teaser": post_text.split("\n\n")[0][:200],
            },
        )
        promoted["history"] = promoted["history"][:50]
        save_promoted(promoted)
        return 1

    log("FAILED | promo tweet did not post (check X credits / tokens)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote Mon/Wed/Fri blog.murmur.red posts on X (text + link)"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Ignore weekday/date gates")
    parser.add_argument("--id", dest="article_id", help="Promote specific article id or URL")
    args = parser.parse_args()
    n = run(dry_run=args.dry_run, force=args.force, article_id=args.article_id)
    if n:
        log(f"DONE | promoted {n} post(s)")


if __name__ == "__main__":
    main()
