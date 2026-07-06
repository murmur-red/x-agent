#!/usr/bin/env python3
"""
Reactive X posts when something big happens in AI.

Checks every run for major AI news (model launches, outages, regulation, big deals).
Posts at most TREND_MAX_PER_WEEK times per week; skips topics already covered by blog.

Usage:
  python3 social/x_trend_watcher.py
  python3 social/x_trend_watcher.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from x_api import log, post_tweet  # noqa: E402

load_dotenv(ROOT / ".env")

SEEN_PATH = Path(__file__).parent / "trends_seen.json"
MAX_PER_WEEK = int(os.getenv("TREND_MAX_PER_WEEK", "2"))

REACTIVE_SYSTEM = """\
You write a short reactive X post for @murmurRed when something big happens in AI.

Voice: operator watching how companies use AI. Sharp, grounded, not hype.
Angle: what this means for teams actually running AI — adoption, cost, ops, risk.
Rules:
- Under 250 characters total
- Reference the specific event by name
- One clear take, not a news summary
- No hashtags, no em dashes, no "breaking"
- Return ONLY the post text
"""

BIG_EVENT_PROMPT = """\
What is the single biggest AI industry event in the last 12 hours?

Only report something genuinely significant:
- Major model launch (GPT, Claude, Gemini, Llama, etc.)
- Large acquisition or funding round (>$500M)
- Major outage affecting AI services
- Significant regulation or policy change
- Surprising benchmark or capability shift

If nothing qualifies, respond with exactly: NONE

If something qualifies, respond as JSON only:
{"event": "short name", "summary": "2 sentences of facts", "significance": "high|medium"}
"""


def load_seen() -> dict:
    if SEEN_PATH.exists():
        return json.loads(SEEN_PATH.read_text())
    return {"events": [], "posts_this_week": []}


def save_seen(data: dict) -> None:
    SEEN_PATH.write_text(json.dumps(data, indent=2))


def week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def posts_this_week(data: dict) -> int:
    ws = week_start().isoformat()
    return sum(1 for p in data.get("posts_this_week", []) if p >= ws)


def scan_ai_news() -> dict | None:
    xai_key = os.getenv("XAI_API_KEY", "")
    if xai_key:
        return _scan_grok(xai_key)
    return _scan_hackernews()


def _scan_grok(api_key: str) -> dict | None:
    r = httpx.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "grok-3",
            "messages": [{"role": "user", "content": BIG_EVENT_PROMPT}],
        },
        timeout=45,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"].strip()
    if text == "NONE" or "NONE" in text[:20]:
        return None
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        data = json.loads(text[start:end])
        if data.get("significance") == "high" or data.get("significance") == "medium":
            return data
    except json.JSONDecodeError:
        pass
    return None


def _scan_hackernews() -> dict | None:
    """Fallback: top HN AI stories with high engagement."""
    try:
        r = httpx.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": "AI OR OpenAI OR Claude OR Gemini OR LLM",
                "tags": "story",
                "numericFilters": "points>200",
                "hitsPerPage": 5,
            },
            timeout=20,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        for hit in hits:
            created = datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc)
            if datetime.now(timezone.utc) - created > timedelta(hours=18):
                continue
            return {
                "event": hit["title"][:80],
                "summary": f"Trending on HN with {hit['points']} points. {hit.get('url', '')}",
                "significance": "medium",
            }
    except Exception as e:
        log(f"TREND SCAN ERROR | {e}")
    return None


def generate_reactive_post(event: dict) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return f"{event['event']}. Worth watching if you run AI in production."

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
    resp = client.messages.create(
        model=model,
        max_tokens=100,
        system=REACTIVE_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(event)}],
    )
    return resp.content[0].text.strip().replace("—", ". ")[:250]


def run(dry_run: bool = False) -> int:
    data = load_seen()
    if posts_this_week(data) >= MAX_PER_WEEK:
        log(f"SKIP | weekly cap ({MAX_PER_WEEK}) reached")
        return 0

    event = scan_ai_news()
    if not event:
        log("SKIP | no significant AI event")
        return 0

    event_key = event["event"].lower()[:80]
    if event_key in [e.lower() for e in data.get("events", [])]:
        log(f"SKIP | already posted about {event['event'][:40]}")
        return 0

    post_text = generate_reactive_post(event)
    log(f"TREND | {event['event'][:60]}")
    tweet_id = post_tweet(post_text, dry_run=dry_run)

    if tweet_id or dry_run:
        data.setdefault("events", []).append(event_key)
        data.setdefault("posts_this_week", []).append(date.today().isoformat())
        save_seen(data)
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Post reactive X content on big AI news")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    n = run(dry_run=args.dry_run)
    if n:
        log(f"DONE | trend post {n}")


if __name__ == "__main__":
    main()