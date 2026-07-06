"""Generate the 4-week X content calendar CSV from x_content.py."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from x_content import (
    BEHIND_THE_SCENES,
    DATA_DROPS,
    ENGAGEMENT_HOOKS,
    HOT_TAKES,
    POLLS,
    THREADS,
    format_post,
)

SLOT_TIMES = {
    "morning": "13:00",
    "noon": "17:00",
    "evening": "21:00",
}

CALENDAR_PATH = Path(__file__).parent / "content_calendar.csv"


def _schedule(start: date) -> list[dict]:
    rows: list[dict] = []
    d = start

    def add(day_offset: int, slot: str, post, week: int, notes: str = ""):
        post_date = d + timedelta(days=day_offset)
        rows.append({
            "date": post_date.isoformat(),
            "time_utc": SLOT_TIMES[slot],
            "week": week,
            "content_type": post.content_type,
            "thread_id": post.thread_id,
            "thread_part": post.thread_part,
            "post_text": format_post(post),
            "media_note": post.media_note or notes,
            "status": "scheduled",
        })

    w = 1
    add(0, "morning", HOT_TAKES[0], w, "Launch — AI strategy vs usage graph")
    for p in THREADS["ai_usage_gap"]:
        add(0, "noon", p, w)
    add(1, "morning", DATA_DROPS[0], w, "Telemetry screenshot")
    add(2, "morning", HOT_TAKES[1], w)
    add(2, "evening", ENGAGEMENT_HOOKS[0], w)
    add(3, "morning", BEHIND_THE_SCENES[0], w)
    add(4, "noon", HOT_TAKES[2], w)
    add(5, "morning", DATA_DROPS[1], w)
    add(6, "evening", POLLS[0], w)

    w = 2
    add(7, "morning", HOT_TAKES[3], w)
    for p in THREADS["ai_ops_playbook"]:
        add(8, "morning" if p.thread_part <= 2 else "noon", p, w)
    add(9, "morning", DATA_DROPS[2], w)
    add(10, "evening", HOT_TAKES[4], w)
    add(11, "morning", BEHIND_THE_SCENES[1], w)
    add(12, "noon", ENGAGEMENT_HOOKS[1], w)
    add(13, "morning", POLLS[1], w)

    w = 3
    for p in THREADS["company_story_bbb"]:
        add(14 + (p.thread_part - 1) // 2, "morning" if p.thread_part % 2 == 1 else "noon", p, w)
    add(16, "evening", HOT_TAKES[0], w, "Repost — new audience")
    add(17, "morning", DATA_DROPS[0], w)
    add(18, "noon", ENGAGEMENT_HOOKS[2], w)
    add(19, "morning", BEHIND_THE_SCENES[2], w)
    add(20, "evening", POLLS[2], w)

    w = 4
    add(21, "morning", HOT_TAKES[1], w, "Evergreen repost")
    add(22, "morning", DATA_DROPS[1], w)
    add(23, "noon", ENGAGEMENT_HOOKS[0], w)
    add(24, "morning", BEHIND_THE_SCENES[0], w)
    add(25, "evening", POLLS[0], w)
    add(26, "morning", HOT_TAKES[4], w)
    add(27, "noon", ENGAGEMENT_HOOKS[2], w)

    rows.sort(key=lambda r: (r["date"], r["time_utc"], r["thread_part"]))
    return rows


def main(start: date | None = None) -> Path:
    start = start or date.today() + timedelta(days=1)
    rows = _schedule(start)
    fieldnames = [
        "date", "time_utc", "week", "content_type", "thread_id",
        "thread_part", "post_text", "media_note", "status",
    ]
    with CALENDAR_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} posts → {CALENDAR_PATH}")
    print(f"Schedule: {start.isoformat()} → {(start + timedelta(days=27)).isoformat()}")
    return CALENDAR_PATH


if __name__ == "__main__":
    main()