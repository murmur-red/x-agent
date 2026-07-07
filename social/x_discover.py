"""Discover X posts via Grok x_search (X API read is blocked on pay-per-use)."""

from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta

import httpx

from x_api import log

XAI_URL = "https://api.x.ai/v1/responses"
TWEET_ID_RE = re.compile(r"/status/(\d+)")


def _xai_key() -> str:
    return os.getenv("XAI_API_KEY", "")


def _extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    for opener, closer in (("[", "]"), ("{", "}")):
        start = text.find(opener)
        end = text.rfind(closer) + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                continue
    return None


def _grok_search(prompt: str, handles: list[str] | None = None) -> tuple[str, list[dict]]:
    key = _xai_key()
    if not key:
        return "", []

    tools: list[dict] = [{"type": "x_search"}]
    if handles:
        tools = [{"type": "x_search", "allowed_x_handles": handles[:20]}]

    payload = {
        "model": os.getenv("XAI_DISCOVER_MODEL", "grok-3"),
        "input": [{"role": "user", "content": prompt}],
        "tools": tools,
    }

    try:
        r = httpx.post(
            XAI_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=int(os.getenv("XAI_DISCOVER_TIMEOUT", "90")),
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        log(f"DISCOVER ERROR | {exc}")
        return "", []

    texts: list[str] = []
    citations: list[dict] = []
    for item in data.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for block in item.get("content", []) or []:
            if block.get("type") == "output_text":
                texts.append(block.get("text", ""))
                for ann in block.get("annotations", []) or []:
                    if ann.get("type") == "url_citation":
                        citations.append(ann)

    return "\n".join(texts), citations


def _normalize_posts(raw, citations: list[dict]) -> list[dict]:
    posts: list[dict] = []

    if isinstance(raw, dict) and raw.get("tweet_id"):
        raw = [raw]
    if not isinstance(raw, list):
        raw = []

    cite_ids = []
    for c in citations:
        url = c.get("url", "")
        m = TWEET_ID_RE.search(url) or re.search(r"/status/(\d+)", url)
        if m:
            cite_ids.append(m.group(1))

    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        tid = item.get("tweet_id") or item.get("id")
        if tid is None and i < len(cite_ids):
            tid = cite_ids[i]
        if tid is None:
            continue
        author = (item.get("author") or item.get("handle") or "").lstrip("@")
        posts.append({
            "tweet_id": str(tid),
            "author": author,
            "text": (item.get("text") or "")[:160],
        })
    return posts


def discover_contributor_posts(handles: list[str], *, max_posts: int = 5) -> list[dict]:
    if not handles:
        return []
    if not _xai_key():
        log("DISCOVER SKIP | no XAI_API_KEY for contributor scan")
        return []

    since = (date.today() - timedelta(days=2)).isoformat()
    handle_str = ", ".join(f"@{h.lstrip('@')}" for h in handles[:20])
    prompt = f"""Find the most recent original tweet (not a reply, not a retweet) from each of these accounts posted since {since}:
{handle_str}

Return JSON array only, at most {max_posts} items total (one per author when possible):
[{{"tweet_id":"numeric id","author":"handle without @","text":"first 120 chars"}}]

Skip accounts with no qualifying post. If none found, return [].
"""
    text, citations = _grok_search(prompt, [h.lstrip("@") for h in handles[:20]])
    parsed = _extract_json(text)
    posts = _normalize_posts(parsed, citations)
    log(f"DISCOVER | contributors — {len(posts)} candidate(s)")
    return posts[:max_posts]


def discover_mentions(my_handle: str = "murmurRed", *, max_posts: int = 10) -> list[dict]:
    if not _xai_key():
        log("DISCOVER SKIP | no XAI_API_KEY for mention scan")
        return []

    since = (date.today() - timedelta(days=7)).isoformat()
    prompt = f"""Find replies and mentions directed at @{my_handle} on X since {since}.
Exclude posts authored by @{my_handle}.

Return JSON array only, max {max_posts} items:
[{{"tweet_id":"numeric id","author":"handle without @","text":"first 120 chars"}}]

If none, return [].
"""
    text, citations = _grok_search(prompt)
    parsed = _extract_json(text)
    posts = _normalize_posts(parsed, citations)
    log(f"DISCOVER | mentions — {len(posts)} candidate(s)")
    return posts[:max_posts]