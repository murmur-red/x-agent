"""Generate the 8-week X content calendar CSV from x_content.py."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from x_content import (
    AGRI_AI_POSTS,
    AI_TECH_POSTS,
    BEHIND_THE_SCENES,
    DATA_DROPS,
    ENGAGEMENT_HOOKS,
    FILLER_ROTATION,
    GLOBAL_AI_POSTS,
    HOT_TAKES,
    HUMOR_POSTS,
    POLLS,
    THREADS,
    WEEK1_LAUNCH,
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
        # Thread parts share one slot — they post as a single batch when due.
        if post.thread_id:
            key = (post_date, time_utc, post.thread_id, post.thread_part)
        else:
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

    # --- Weeks 1–4: anchor content ---
    w = 1
    add(0, "launch", WEEK1_LAUNCH, w, "Voice relaunch — 13:00 Amsterdam")
    lay_thread(0, "noon", "ai_usage_gap", w)
    add(1, "morning", AI_TECH_POSTS[0], w, "AI + tech")
    add(1, "evening", HUMOR_POSTS[0], w, "humor")
    add(2, "morning", GLOBAL_AI_POSTS[0], w, "developed countries")
    add(2, "evening", ENGAGEMENT_HOOKS[1], w)
    add(3, "morning", AGRI_AI_POSTS[0], w, "agriculture AI")
    add(3, "noon", HOT_TAKES[1], w)
    add(4, "morning", AI_TECH_POSTS[2], w)
    add(4, "evening", HUMOR_POSTS[2], w)
    add(5, "morning", GLOBAL_AI_POSTS[2], w)
    add(5, "noon", HOT_TAKES[2], w)
    add(6, "morning", AGRI_AI_POSTS[2], w)
    add(6, "evening", POLLS[0], w)

    w = 2
    add(7, "morning", GLOBAL_AI_POSTS[4], w)
    add(7, "evening", HUMOR_POSTS[4], w)
    for p in THREADS["ai_ops_playbook"]:
        add(8, "morning" if p.thread_part <= 2 else "noon", p, w)
    add(9, "morning", AI_TECH_POSTS[4], w)
    add(10, "evening", HOT_TAKES[3], w)
    add(11, "morning", AGRI_AI_POSTS[4], w)
    add(12, "noon", ENGAGEMENT_HOOKS[0], w)
    add(13, "morning", DATA_DROPS[0], w, "telemetry — week 2")
    add(13, "evening", POLLS[1], w)

    w = 3
    for p in THREADS["company_story_bbb"]:
        add(14 + (p.thread_part - 1) // 2, "morning" if p.thread_part % 2 == 1 else "noon", p, w)
    add(16, "evening", AGRI_AI_POSTS[6], w, "ag tech story")
    add(17, "morning", GLOBAL_AI_POSTS[6], w)
    add(18, "noon", HUMOR_POSTS[6], w)
    add(19, "morning", AI_TECH_POSTS[6], w)
    add(20, "evening", POLLS[2], w)

    w = 4
    add(21, "morning", HOT_TAKES[4], w)
    add(22, "morning", AGRI_AI_POSTS[8], w)
    add(23, "noon", GLOBAL_AI_POSTS[8], w)
    add(24, "morning", ENGAGEMENT_HOOKS[2], w)
    add(25, "evening", HUMOR_POSTS[8], w)
    add(26, "morning", BEHIND_THE_SCENES[0], w)
    add(27, "noon", AI_TECH_POSTS[8], w)

    # --- Weeks 5–8: repeat threads + fresh singles ---
    w = 5
    lay_thread(28, "noon", "ai_usage_gap", w)
    add(29, "morning", GLOBAL_AI_POSTS[1], w)
    add(30, "evening", AGRI_AI_POSTS[1], w)
    add(31, "morning", HUMOR_POSTS[1], w)
    add(32, "noon", AI_TECH_POSTS[1], w)
    add(33, "evening", POLLS[0], w)

    w = 6
    for p in THREADS["ai_ops_playbook"]:
        add(35, "morning" if p.thread_part <= 2 else "noon", p, w)
    add(36, "morning", AGRI_AI_POSTS[3], w)
    add(37, "evening", GLOBAL_AI_POSTS[3], w)
    add(38, "morning", HUMOR_POSTS[3], w)
    add(39, "noon", DATA_DROPS[1], w)
    add(40, "evening", POLLS[2], w)

    w = 7
    for p in THREADS["company_story_bbb"]:
        add(42 + (p.thread_part - 1) // 2, "morning" if p.thread_part % 2 == 1 else "noon", p, w)
    add(44, "evening", AI_TECH_POSTS[5], w)
    add(45, "morning", GLOBAL_AI_POSTS[5], w)
    add(46, "noon", AGRI_AI_POSTS[5], w)
    add(47, "morning", ENGAGEMENT_HOOKS[1], w)

    w = 8
    add(49, "morning", HOT_TAKES[0], w, "Month-2 evergreen")
    add(50, "evening", HUMOR_POSTS[10], w)
    add(51, "morning", AI_TECH_POSTS[9], w)
    add(52, "noon", AGRI_AI_POSTS[9], w)
    add(53, "evening", GLOBAL_AI_POSTS[9], w)
    add(54, "morning", BEHIND_THE_SCENES[1], w)
    add(55, "evening", POLLS[1], w)

    # --- Daily fill: broader AI/tech + humor rotation ---
    for day in range(NUM_WEEKS * 7):
        week = day // 7 + 1
        if day == 0:
            continue  # launch day only
        filler = FILLER_ROTATION[day % len(FILLER_ROTATION)]
        add(day, "early", filler, week)
        add(day, "noon", FILLER_ROTATION[(day + 11) % len(FILLER_ROTATION)], week)
        if day % 2 == 0:
            add(day, "evening", HUMOR_POSTS[day % len(HUMOR_POSTS)], week)

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