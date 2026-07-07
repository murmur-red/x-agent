"""Generate the 8-week X content calendar CSV from x_content.py."""

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
    QUICK_TAKES,
    THREADS,
    format_post,
)

SLOT_TIMES = {
    "launch": "11:00",  # 13:00 Europe/Amsterdam (CEST)
    "early": "09:00",
    "morning": "13:00",
    "noon": "17:00",
    "evening": "21:00",
}

NUM_WEEKS = 8
CALENDAR_PATH = Path(__file__).parent / "content_calendar.csv"


def _schedule(start: date) -> list[dict]:
    rows: list[dict] = []
    occupied: set[tuple[str, str]] = set()
    d = start

    def add(day_offset: int, slot: str, post, week: int, notes: str = "") -> None:
        post_date = (d + timedelta(days=day_offset)).isoformat()
        time_utc = SLOT_TIMES[slot]
        key = (post_date, time_utc)
        if key in occupied:
            return
        occupied.add(key)
        rows.append({
            "date": post_date,
            "time_utc": time_utc,
            "week": week,
            "content_type": post.content_type,
            "thread_id": post.thread_id,
            "thread_part": post.thread_part,
            "post_text": format_post(post),
            "media_note": post.media_note or notes,
            "status": "scheduled",
        })

    def lay_thread(day_offset: int, slot: str, thread_key: str, week: int) -> None:
        for part in THREADS[thread_key]:
            add(day_offset, slot, part, week)

    # --- Weeks 1–4: anchor content (threads, polls, launches) ---
    w = 1
    add(0, "launch", HOT_TAKES[0], w, "Go live — 13:00 Amsterdam")
    lay_thread(0, "noon", "ai_usage_gap", w)
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

    # --- Weeks 5–8: repeat threads + fresh singles ---
    w = 5
    lay_thread(28, "noon", "ai_usage_gap", w)
    add(29, "morning", HOT_TAKES[2], w)
    add(30, "evening", ENGAGEMENT_HOOKS[1], w)
    add(31, "morning", DATA_DROPS[2], w)
    add(32, "noon", BEHIND_THE_SCENES[1], w)
    add(33, "evening", POLLS[1], w)

    w = 6
    for p in THREADS["ai_ops_playbook"]:
        add(35, "morning" if p.thread_part <= 2 else "noon", p, w)
    add(36, "morning", HOT_TAKES[3], w)
    add(37, "evening", DATA_DROPS[0], w)
    add(38, "morning", ENGAGEMENT_HOOKS[2], w)
    add(39, "noon", BEHIND_THE_SCENES[2], w)
    add(40, "evening", POLLS[2], w)

    w = 7
    for p in THREADS["company_story_bbb"]:
        add(42 + (p.thread_part - 1) // 2, "morning" if p.thread_part % 2 == 1 else "noon", p, w)
    add(44, "evening", HOT_TAKES[1], w)
    add(45, "morning", DATA_DROPS[1], w)
    add(46, "noon", ENGAGEMENT_HOOKS[0], w)
    add(47, "morning", BEHIND_THE_SCENES[0], w)

    w = 8
    add(49, "morning", HOT_TAKES[0], w, "Month-2 evergreen")
    add(50, "evening", POLLS[0], w)
    add(51, "morning", DATA_DROPS[2], w)
    add(52, "noon", HOT_TAKES[4], w)
    add(53, "evening", ENGAGEMENT_HOOKS[1], w)
    add(54, "morning", BEHIND_THE_SCENES[1], w)
    add(55, "evening", POLLS[2], w)

    # --- Daily fill: 09:00 quick take + extra evening/noon on open slots ---
    fillers = QUICK_TAKES + HOT_TAKES + DATA_DROPS
    for day in range(NUM_WEEKS * 7):
        week = day // 7 + 1
        if day == 0:
            continue  # launch day: 11:00 Amsterdam only (no early filler)
        add(day, "early", fillers[day % len(fillers)], week)
        if day % 2 == 0:
            add(day, "noon", fillers[(day + 5) % len(fillers)], week)
        if day % 3 == 1:
            add(day, "evening", ENGAGEMENT_HOOKS[day % len(ENGAGEMENT_HOOKS)], week)

    rows.sort(key=lambda r: (r["date"], r["time_utc"], int(r["thread_part"] or 0)))
    return rows


def main(start: date | None = None) -> Path:
    start = start or date.today()
    rows = _schedule(start)
    fieldnames = [
        "date", "time_utc", "week", "content_type", "thread_id",
        "thread_part", "post_text", "media_note", "status",
    ]
    with CALENDAR_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    end = start + timedelta(days=NUM_WEEKS * 7 - 1)
    print(f"Wrote {len(rows)} posts → {CALENDAR_PATH}")
    print(f"Schedule: {start.isoformat()} → {end.isoformat()} ({NUM_WEEKS} weeks)")
    return CALENDAR_PATH


if __name__ == "__main__":
    main()