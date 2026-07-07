"""
murmur.red X content library — AI ops energy, minimal CS jargon.

Voice: operator watching how companies buy AI vs actually run it.
Topics: AI adoption, usage telemetry, token economics, ops reality.
Companies: what they deploy, what sticks, what quietly dies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

BRAND = {
    "handle": "@murmur_red",
    "url": "https://murmur.red",
    "tagline": "AI ops telemetry",
    "bio": (
        "How companies buy AI vs how they actually use it. "
        "Usage, cost, adoption — in numbers. 🔥 murmur.red"
    ),
    "pinned_thread_hook": (
        "Every company bought the AI license. Half are barely running inference. "
        "A thread on the usage gap 🧵"
    ),
}

# Demo portfolio — reframed as AI adoption patterns, not CS accounts
COMPANY_PATTERNS = {
    "BBB": {
        "industry": "Media",
        "contract": "$520K/yr AI platform",
        "usage": "100 → 54 token units in 6 months",
        "story": "Team built an in-house workflow tool; AI calls migrated quietly",
    },
    "YYY": {
        "industry": "Logistics",
        "contract": "$480K/yr",
        "usage": "95 → 52 tokens (-45%)",
        "story": "Internal reorg; nobody owned the AI rollout anymore",
    },
    "AAA": {
        "industry": "Manufacturing",
        "contract": "$360K/yr",
        "usage": "70 → 96 tokens (+37%)",
        "story": "Agentic automation compounding — the rollout that actually stuck",
    },
}

PORTFOLIO = {
    "licensed_spend": "$2.5M",
    "actual_usage": "$2.11M run-rate",
    "idle_gap": "$390K",
    "companies_fading": "2 of 5",
    "gap_pct": "15.6%",
}


@dataclass(frozen=True)
class Post:
    text: str
    content_type: str
    thread_id: str = ""
    thread_part: int = 0
    media_note: str = ""
    hashtags: str = "#AI #AIOps #LLM #BuildInPublic"


HOT_TAKES: list[Post] = [
    Post(
        "Every company has an AI strategy deck.\n\n"
        "Fewer have an AI *usage* graph.\n\n"
        "The gap between what you bought and what your teams actually run "
        "is where margin, momentum, and surprise live.\n\n"
        "murmur.red",
        "single",
    ),
    Post(
        "Hot take: the AI rollout isn't failing in the demo.\n\n"
        "It's failing in week 9 — when the pilot team moves on, "
        "the API key stays active, and nobody checks the dashboard.\n\n"
        "Usage telemetry > launch announcement.",
        "single",
    ),
    Post(
        "Your inference bill is a honesty meter.\n\n"
        "Spike = people found a workflow that works.\n"
        "Flatline = shelfware with a logo on it.\n\n"
        "Tokens don't care about your press release.",
        "single",
    ),
    Post(
        "Plot twist: the company didn't cancel AI.\n\n"
        "They just stopped calling it.\n\n"
        "Contract still active ✅\n"
        "Dashboard still green ✅\n"
        "Inference down 46% over 6 months ❌\n\n"
        "Different problem. Different fix.",
        "single",
    ),
    Post(
        "Build vs buy AI is the wrong frame.\n\n"
        "The real question: build vs buy vs *actually operate*.\n\n"
        "Most companies nail procurement.\n"
        "Almost nobody owns the ops layer after go-live.",
        "single",
    ),
]

DATA_DROPS: list[Post] = [
    Post(
        f"📊 AI usage telemetry (demo portfolio, real math):\n\n"
        f"Licensed spend:  {PORTFOLIO['licensed_spend']}\n"
        f"Actual usage:    {PORTFOLIO['actual_usage']}\n"
        f"Idle gap:        {PORTFOLIO['idle_gap']}\n"
        f"Fading:          {PORTFOLIO['companies_fading']}\n\n"
        f"{PORTFOLIO['gap_pct']} of your AI budget might be ambient noise.",
        "single",
        media_note="screenshot index.html telemetry cards",
    ),
    Post(
        "The 90-day pattern:\n\n"
        "If inference drops >15% while the contract still runs,\n"
        "the tool didn't fail — the workflow did.\n\n"
        "Catch it in ops review. Not at the board slide.",
        "single",
    ),
    Post(
        "MoM inference velocity: -2% sounds tiny.\n\n"
        "Over 6 months on a $520K AI platform?\n"
        "That's a quarter-million in usage that evaporated.\n"
        "Procurement still shows full contract.\n\n"
        "Paper vs reality.",
        "single",
    ),
]

THREADS: dict[str, list[Post]] = {
    "ai_usage_gap": [
        Post(
            "Every company bought the AI license.\n"
            "Half are barely running inference.\n\n"
            "A thread on the AI usage gap 🧵",
            "thread",
            thread_id="ai_usage_gap",
            thread_part=1,
        ),
        Post(
            "1/ The usage gap ≠ cancellation.\n\n"
            "It's the company that:\n"
            "• Still pays for the platform\n"
            "• Still lists AI in the annual report\n"
            "• Quietly stopped calling the API\n\n"
            "Then budget season hits and everyone acts confused.",
            "thread",
            thread_id="ai_usage_gap",
            thread_part=2,
        ),
        Post(
            "2/ Licensed spend is the *budget line*.\n\n"
            "Run-rate usage is what teams actually consume.\n\n"
            "When usage < spend, you have shelfware with momentum problems — "
            "not a technology problem.",
            "thread",
            thread_id="ai_usage_gap",
            thread_part=3,
        ),
        Post(
            "3/ Signals worth watching in AI ops:\n\n"
            "→ Inference decay (month over month)\n"
            "→ Usage ratio (actual / licensed)\n"
            "→ Active seats vs provisioned\n"
            "→ Who owns the workflow after pilot ends\n"
            "→ Whether the legal entity still exists 🚨",
            "thread",
            thread_id="ai_usage_gap",
            thread_part=4,
        ),
        Post(
            "4/ Real pattern from our demo data:\n\n"
            "Media company. $520K AI platform.\n"
            "Inference: 100 → 54 in 6 months.\n"
            "Internal team built a replacement workflow.\n"
            "Nobody updated the ops map.\n\n"
            "Verdict: fading adoption. Not a bug report.",
            "thread",
            thread_id="ai_usage_gap",
            thread_part=5,
        ),
        Post(
            "5/ The fix isn't another pilot.\n\n"
            "It's usage telemetry + identity checks + an AI loop "
            "that commits to a read with numbers — not vibes.\n\n"
            "We built it at murmur.red\n\n"
            "RT if your AI dashboard looks healthier than your inference graph.",
            "thread",
            thread_id="ai_usage_gap",
            thread_part=6,
        ),
    ],
    "ai_ops_playbook": [
        Post(
            "Most AI rollouts die after the demo video.\n\n"
            "Here's the ops playbook that keeps inference alive 🧵",
            "thread",
            thread_id="ai_ops_playbook",
            thread_part=1,
        ),
        Post(
            "1/ Stop measuring launches.\n"
            "Start measuring inference.\n\n"
            "If monthly API calls trend negative for 3+ months, "
            "the workflow lost — regardless of what the survey said.",
            "thread",
            thread_id="ai_ops_playbook",
            thread_part=2,
        ),
        Post(
            "2/ The 85% usage rule.\n\n"
            "Actual consumption / licensed spend < 0.85?\n"
            "Something changed in how the company runs AI.\n"
            "Find out what before the next budget cycle.",
            "thread",
            thread_id="ai_ops_playbook",
            thread_part=3,
        ),
        Post(
            "3/ Reorg = adoption risk.\n\n"
            "No new owner for the AI workflow within 30 days?\n"
            "Inference decay accelerates.\n"
            "Assign an ops owner + business sponsor immediately.",
            "thread",
            thread_id="ai_ops_playbook",
            thread_part=4,
        ),
        Post(
            "4/ One action per company. Not a roadmap.\n\n"
            "Owner + measurable outcome + deadline.\n"
            "'Map which team still calls the API' beats "
            "'drive AI adoption' every time.",
            "thread",
            thread_id="ai_ops_playbook",
            thread_part=5,
        ),
        Post(
            "5/ We run a generator-critic loop on usage data:\n\n"
            "Generate read → critic attacks → revise with evidence.\n\n"
            "No vague 'low engagement.' Only numbers.\n\n"
            "Live simulator: murmur.red",
            "thread",
            thread_id="ai_ops_playbook",
            thread_part=6,
        ),
    ],
    "company_story_bbb": [
        Post(
            "🏭 Company story (demo data, anonymized):\n\n"
            "Media company. Big AI platform contract.\n"
            "This is what fading adoption actually looks like 🧵",
            "thread",
            thread_id="company_bbb",
            thread_part=1,
        ),
        Post(
            "Month 1: $520K contract. 100 inference units. 100 seats.\n"
            "Month 6: 54 units. 41 active users.\n\n"
            "Ops dashboard: 🟢 fine\n"
            "Support volume: high\n"
            "Workflow owner: gone",
            "thread",
            thread_id="company_bbb",
            thread_part=2,
        ),
        Post(
            "The team didn't quit AI loudly.\n"
            "They just... routed around it.\n\n"
            "Internal tool absorbed the workflow.\n"
            "API calls dropped. Nobody updated the runbook.",
            "thread",
            thread_id="company_bbb",
            thread_part=3,
        ),
        Post(
            "Registry check: legal entity flagged dissolved.\n\n"
            "Contract still running.\n"
            "Inference still decaying.\n"
            "Budget line still full.\n\n"
            "Three dashboards. Three stories.",
            "thread",
            thread_id="company_bbb",
            thread_part=4,
        ),
        Post(
            "The lesson:\n\n"
            "Buying AI ≠ operating AI.\n"
            "Watch inference. Watch ownership. Watch identity.\n\n"
            "murmur.red — usage telemetry for companies that ship AI.",
            "thread",
            thread_id="company_bbb",
            thread_part=5,
        ),
    ],
}

POLLS: list[Post] = [
    Post(
        "What's the first sign AI adoption is fading?\n\n"
        "🔴 Inference decay\n"
        "🟡 Workflow owner left\n"
        "🟢 Active users dropping\n"
        "⚫ 'We're still exploring use cases'",
        "poll",
    ),
    Post(
        "Honest question for ops leaders:\n\n"
        "Does your AI spend match actual usage?\n\n"
        "📊 Yes — we track inference\n"
        "😬 Sometimes — we catch it late\n"
        "💀 No idea — we track the contract",
        "poll",
    ),
    Post(
        "Where is your company on AI right now?\n\n"
        "🧪 Piloting\n"
        "📈 Scaling what works\n"
        "💸 Paying for shelfware\n"
        "🔧 Building in-house instead",
        "poll",
    ),
]

ENGAGEMENT_HOOKS: list[Post] = [
    Post(
        "Drop the AI tool your company bought but barely uses.\n\n"
        "I'll start: enterprise platform, -46% inference over 6 months, "
        "internal replacement built quietly. Dashboard still green. 💀",
        "single",
    ),
    Post(
        "Ops people — what do you wish leadership actually measured on AI?\n\n"
        "(Mine: inference trend. Not slide count.)",
        "single",
    ),
    Post(
        "Building in public: usage telemetry for AI-powered companies.\n\n"
        "Demo portfolio: $2.5M licensed, $390K idle gap.\n\n"
        "What should we instrument next? 👇",
        "single",
    ),
]

QUICK_TAKES: list[Post] = [
    Post(
        "Pilot success ≠ production adoption.\n\n"
        "The handoff from demo team to ops is where most AI budgets go to die.",
        "single",
    ),
    Post(
        "Three numbers every AI ops lead should see weekly:\n\n"
        "1. Inference MoM %\n"
        "2. Active users / licensed seats\n"
        "3. Cost per successful workflow run",
        "single",
    ),
    Post(
        "Your AI vendor's NPS survey won't tell you the workflow died.\n\n"
        "Your inference graph will.",
        "single",
    ),
    Post(
        "Shelfware isn't cancelled software.\n\n"
        "It's software still on the invoice while the team routes around it.",
        "single",
    ),
    Post(
        "The quiet killer: same contract, fewer API calls, no incident ticket.\n\n"
        "That's not stability. That's fading adoption.",
        "single",
    ),
    Post(
        "AI procurement asks: 'What did we buy?'\n\n"
        "AI ops should ask: 'What still runs on Monday morning?'",
        "single",
    ),
    Post(
        "Token spend without workflow ownership is just expensive hope.",
        "single",
    ),
    Post(
        "If nobody owns the AI workflow after go-live,\n"
        "inference decay isn't a surprise — it's the default.",
        "single",
    ),
    Post(
        "Companies track AI licenses.\n\n"
        "Few track whether anyone still calls the API on a random Tuesday.",
        "single",
    ),
    Post(
        "Week 9 problem: pilot team moved on, dashboard still green, "
        "budget still committed, usage already sliding.",
        "single",
    ),
    Post(
        "Good AI ops isn't more dashboards.\n\n"
        "It's one honest graph: licensed spend vs actual inference.",
        "single",
    ),
    Post(
        "The best AI rollout signal isn't a launch tweet.\n\n"
        "It's whether usage holds 90 days after the press release.",
        "single",
    ),
]

BEHIND_THE_SCENES: list[Post] = [
    Post(
        "Shipped: generator-critic loop on usage data.\n\n"
        "Claude reads the numbers → critic attacks the take → revise with evidence.\n\n"
        "No more 'looks healthy' without citing inference, MoM %, or day count.",
        "single",
    ),
    Post(
        "We cross-check every company against public registries.\n\n"
        "Identity health for B2B AI contracts.\n"
        "Because sometimes the org paying for inference doesn't legally exist anymore.\n\n"
        "🇳🇱 Registry data > gut feel.",
        "single",
    ),
    Post(
        "New page: economics of running AI inside a company.\n\n"
        "Headcount vs revenue vs inference cost.\n"
        "What you can actually afford to operate.\n"
        "Break-even with fading adoption baked in.\n\n"
        "murmur.red",
        "single",
    ),
]

WEEKLY_THEMES = {
    1: "Launch — AI usage gap thread + hot takes",
    2: "AI ops — how companies should run inference",
    3: "Company stories — fading adoption patterns",
    4: "Community — polls, building in public",
    5: "Deep dive — usage gap (repeat for new followers)",
    6: "Ops playbook + quick takes",
    7: "Company patterns + engagement",
    8: "Evergreen hits + polls",
}


def all_posts() -> Iterator[Post]:
    for p in HOT_TAKES + DATA_DROPS + POLLS + ENGAGEMENT_HOOKS + BEHIND_THE_SCENES:
        yield p
    for thread in THREADS.values():
        for p in thread:
            yield p


def format_post(post: Post, include_hashtags: bool = False) -> str:
    text = post.text
    if include_hashtags and post.content_type == "single":
        if len(text) + len(post.hashtags) + 2 <= 280:
            text = f"{text}\n\n{post.hashtags}"
    return text


ACCOUNT_SETUP_STEPS = """
╔══════════════════════════════════════════════════════════════╗
║  murmur.red X Account Setup (do this once, ~10 min)         ║
╠══════════════════════════════════════════════════════════════╣
║  1. Go to x.com/i/flow/signup                                ║
║  2. Handle: @murmur_red                                      ║
║  3. Display name: murmur.red                                 ║
║  4. Bio: (copy from BRAND['bio'] in x_content.py)            ║
║  5. Profile pic: crimson #e11d48 on obsidian #0c0a0a         ║
║  6. Banner: AI ops telemetry aesthetic                        ║
║  7. Link: murmur.red                                         ║
║  8. Pin the ai_usage_gap thread (post via scheduler)         ║
║  9. Follow: @OpenAI @AnthropicAI @simonw @swyx @amasad       ║
║ 10. Enable 2FA                                               ║
║ 11. developer.x.com → create app → get API keys → .env       ║
╚══════════════════════════════════════════════════════════════╝
"""