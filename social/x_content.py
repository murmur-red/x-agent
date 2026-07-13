"""
murmur.red X content library — human operator voice across AI, tech, and the real world.

Topics: enterprise AI ops, general tech, developed-world adoption, agriculture AI,
with dry humor and plain language. No corporate speak, no link spam.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

BRAND = {
    "handle": "@murmur_red",
    "url": "https://murmur.red",
    "tagline": "AI in the wild — offices, farms, and dashboards that lie",
    "bio": (
        "AI ops, tech, and the gap between the slide deck and Tuesday morning. "
        "Enterprise usage, global adoption, ag tech. Occasionally funny."
    ),
    "pinned_thread_hook": (
        "Every company bought the AI license. Half are barely running inference. "
        "A thread on the usage gap 🧵"
    ),
    "voice_rules": [
        "Sound like a person, not a press release.",
        "One idea per post. Short lines. Okay to be wry or self-deprecating.",
        "Dry humor > hype. Observation > pitch. No 'excited to announce'.",
        "Mix: enterprise usage, AI/tech news angles, developed countries, agriculture.",
        "No URLs in calendar posts (avoids link preview cards).",
        "Specific beats vague: 'week 9' beats 'digital transformation'.",
    ],
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
        "is where margin, momentum, and surprise live.",
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
            "5/ The fix isn't another pilot deck.\n\n"
            "It's someone watching inference like they'd watch cash flow.\n"
            "Boring job. High leverage.\n\n"
            "If your dashboard looks healthier than your usage graph, "
            "you're measuring procurement — not adoption.",
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
            "5/ Ops habit that actually helps:\n\n"
            "One graph. Licensed spend vs real usage.\n"
            "One owner. One weekly check.\n"
            "One honest sentence for leadership — even if it's awkward.",
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
            "The contract renews. The workflow quietly leaves.\n"
            "Someone should be watching that. Often nobody is.",
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
        "Honest question — no vendor pitch:\n\n"
        "Where have you actually seen AI work outside a demo?\n"
        "Office, farm, hospital, warehouse — curious what's real.",
        "single",
    ),
    Post(
        "Wrong answers only:\n\n"
        "Best signal that your AI rollout succeeded?",
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

AI_TECH_POSTS: list[Post] = [
    Post(
        "LLM didn't hallucinate.\n"
        "It confidently described a department that dissolved in 2019.\n\n"
        "We've all been there.",
        "single",
    ),
    Post(
        "2026 tech stack:\n"
        "Postgres, Kubernetes, three copilots opened once in March,\n"
        "and one person who still knows where the cron jobs live.",
        "single",
    ),
    Post(
        "Every AI keynote: 'this changes everything.'\n"
        "Every ops channel six months later: 'who owns the API key?'",
        "single",
    ),
    Post(
        "GPU shortage solved the wrong problem.\n"
        "We still can't explain what half the models are doing on Tuesdays.",
        "single",
    ),
    Post(
        "Open-source model drops are like free puppies.\n"
        "Adorable announcement. Someone still feeds it GPUs at 2am.",
        "single",
    ),
    Post(
        "Tech Twitter when a new benchmark drops:\n"
        "📈 numbers go up\n"
        "🧍 production workflows unchanged",
        "single",
    ),
    Post(
        "The most underrated AI feature is still 'Ctrl+Z'\n"
        "because the model already emailed three clients.",
        "single",
    ),
    Post(
        "Robots in warehouses: impressive.\n"
        "Robots in slide decks: undefeated.",
        "single",
    ),
    Post(
        "AI safety discourse is important.\n"
        "So is the mundane safety of not piping prod data into a chat box.",
        "single",
    ),
    Post(
        "Semiconductor news today.\n"
        "My plants tomorrow.\n"
        "Same energy: everyone wants capacity, nobody wants maintenance.",
        "single",
    ),
]

GLOBAL_AI_POSTS: list[Post] = [
    Post(
        "US enterprise AI playbook:\n"
        "$2M contract → 12-person pilot → reorg → "
        "dashboard green, usage somewhere else.",
        "single",
    ),
    Post(
        "Nordic AI governance: thoughtful whitepaper, calm committee,\n"
        "then someone runs the real workflow in a spreadsheet anyway.",
        "single",
    ),
    Post(
        "UK public sector AI:\n"
        "beautiful principles document,\n"
        "procurement cycle longer than the model's entire lifespan.",
        "single",
    ),
    Post(
        "Germany: engineering-grade caution on AI.\n"
        "Also engineering-grade Excel exports nobody audits.",
        "single",
    ),
    Post(
        "Japan's factory AI adoption is underrated.\n"
        "Less keynote. More 'this line stops costing us money.'",
        "single",
    ),
    Post(
        "Netherlands: 11 apps to book a dentist,\n"
        "one AI that summarizes why you still didn't go.",
        "single",
    ),
    Post(
        "Singapore treats AI like infrastructure.\n"
        "A lot of places treat it like confetti for the annual report.",
        "single",
    ),
    Post(
        "Developed countries don't lack AI tools.\n"
        "They lack boring owners for boring workflows after go-live.",
        "single",
    ),
    Post(
        "EU AI Act conversations: serious, necessary, slow.\n"
        "Meanwhile teams still share API keys in a Slack thread named 'temp'.",
        "single",
    ),
    Post(
        "Silicon Valley ships the demo.\n"
        "Operations in the rest of the world ships Tuesday.",
        "single",
    ),
]

AGRI_AI_POSTS: list[Post] = [
    Post(
        "Precision ag pitch: every plant individually monitored.\n"
        "Field reality: one sensor offline, dashboard says 🟢, "
        "farmer trusts the neighbor's rain feeling.",
        "single",
    ),
    Post(
        "AI drone maps the field.\n"
        "Model flags blight.\n"
        "Farmer checks the corner that always lies to the algorithm.",
        "single",
    ),
    Post(
        "Developed countries fund ag AI with grants and pilots.\n"
        "Farmers fund intuition until the intuition is wrong — then both learn.",
        "single",
    ),
    Post(
        "Satellite + ML crop forecast: elegant.\n"
        "Actual decision: weather app, gut, and whether the tractor sounds right.",
        "single",
    ),
    Post(
        "Smart irrigation sold the dream of perfect water math.\n"
        "Reality: a clogged line and a very human Saturday.",
        "single",
    ),
    Post(
        "AI in agriculture isn't magic.\n"
        "It's logistics, weather, margins, and machinery older than the model card.",
        "single",
    ),
    Post(
        "Big ag tech demos in climate-controlled rooms.\n"
        "Small farms debug in mud with gloves on. Different test environment.",
        "single",
    ),
    Post(
        "Yield prediction models love clean data.\n"
        "Soil loves surprises. Marriage of inconvenience.",
        "single",
    ),
    Post(
        "The best ag AI I've seen didn't wow a conference.\n"
        "It stopped one expensive mistake before harvest week.",
        "single",
    ),
    Post(
        "We talk AI for farms in rich countries.\n"
        "Worth asking: who maintains the model when the agronomist retires?",
        "single",
    ),
]

HUMOR_POSTS: list[Post] = [
    Post(
        "AI strategy deck: transformative.\n"
        "Usage graph: opened twice, blamed intern, renewed anyway.",
        "single",
    ),
    Post(
        "My favorite enterprise metric is 'active seats'\n"
        "because it measures procurement, not humans.",
        "single",
    ),
    Post(
        "ChatGPT for emails: great.\n"
        "ChatGPT for legal, finance, and HR without review: see you in discovery.",
        "single",
    ),
    Post(
        "We don't need AGI to cause incidents.\n"
        "Regular CI with auto-deploy already does fine.",
        "single",
    ),
    Post(
        "Pilot team mood: 🚀\n"
        "Week 9 ops mood: 🫠\n"
        "Finance mood: ✅ renewed",
        "single",
    ),
    Post(
        "Machine learning team: 'it's learning.'\n"
        "Finance: 'from what budget line?'",
        "single",
    ),
    Post(
        "Hot take: your AI vendor's NPS survey is fine.\n"
        "Your inference graph is the breakup text.",
        "single",
    ),
    Post(
        "If the AI rollout succeeded, you wouldn't need six synonyms for 'adoption' in the QBR.",
        "single",
    ),
    Post(
        "Ag tech AI and enterprise AI share a problem:\n"
        "beautiful dashboard, suspiciously quiet API.",
        "single",
    ),
    Post(
        "I asked leadership for an AI usage graph.\n"
        "They sent a strategy PDF. Different genre.",
        "single",
    ),
    Post(
        "Tech prediction for this year:\n"
        "more models, same number of people who enjoy reading logs.",
        "single",
    ),
    Post(
        "Building AI is hard.\n"
        "Explaining why nobody uses it is a full-time career.",
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
        "Shipping a page on the economics of running AI inside a company.\n\n"
        "Headcount vs revenue vs inference cost.\n"
        "Spoiler: the spreadsheet is the real product.",
        "single",
    ),
]

WEEKLY_THEMES = {
    1: "Launch + usage gap — human operator voice",
    2: "Developed-world AI + enterprise ops",
    3: "Agriculture AI + company stories",
    4: "Tech humor + community polls",
    5: "Global adoption + usage gap (repeat)",
    6: "Ag tech + ops playbook",
    7: "AI/tech takes + engagement",
    8: "Evergreen hits + humor",
}

# Rotating filler pools — weighted toward broader AI/tech + humor
FILLER_ROTATION: list[Post] = (
    AI_TECH_POSTS
    + GLOBAL_AI_POSTS
    + AGRI_AI_POSTS
    + HUMOR_POSTS
    + QUICK_TAKES
    + HOT_TAKES
)


def all_posts() -> Iterator[Post]:
    for p in (
        HOT_TAKES
        + AI_TECH_POSTS
        + GLOBAL_AI_POSTS
        + AGRI_AI_POSTS
        + HUMOR_POSTS
        + DATA_DROPS
        + POLLS
        + ENGAGEMENT_HOOKS
        + BEHIND_THE_SCENES
        + QUICK_TAKES
    ):
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