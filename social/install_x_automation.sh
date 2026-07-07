#!/usr/bin/env bash
# Install all X automation: calendar, blog promoter, trend watcher.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-$(command -v python3)}"
LOG="$ROOT/social/post.log"
UID_NUM="$(id -u)"
AGENTS="$HOME/Library/LaunchAgents"

install_plist() {
    local label="$1" src="$2" script="$3"
    local dst="$AGENTS/${label}.plist"
    sed \
        -e "s|__PYTHON__|$PYTHON|g" \
        -e "s|__SCRIPT__|$script|g" \
        -e "s|__WORKDIR__|$ROOT|g" \
        -e "s|__LOG__|$LOG|g" \
        "$src" > "$dst"
    launchctl bootout "gui/$UID_NUM/$label" 2>/dev/null || true
    launchctl bootstrap "gui/$UID_NUM" "$dst"
    launchctl enable "gui/$UID_NUM/$label"
    echo "  ✓ $label"
}

echo "▸ Installing deps..."
"$PYTHON" -m pip install -q -r "$ROOT/requirements.txt"

echo "▸ Verifying X API..."
"$PYTHON" "$ROOT/x_scheduler.py" status

echo "▸ Building content calendar..."
"$PYTHON" "$ROOT/x_scheduler.py" calendar

mkdir -p "$ROOT/social"
touch "$LOG"

echo "▸ Installing launchd agents..."
install_plist "com.murmur.red.xscheduler" \
    "$ROOT/social/com.murmur.red.xscheduler.plist" \
    "$ROOT/x_scheduler.py post"

install_plist "com.murmur.red.blogpromoter" \
    "$ROOT/social/com.murmur.red.blogpromoter.plist" \
    "$ROOT/social/x_blog_promoter.py"

install_plist "com.murmur.red.trendwatcher" \
    "$ROOT/social/com.murmur.red.trendwatcher.plist" \
    "$ROOT/social/x_trend_watcher.py"

launchctl kickstart -k "gui/$UID_NUM/com.murmur.red.xscheduler" 2>/dev/null || true

echo ""
echo "✅ X automation live:"
echo "   Calendar posts  — every 10 min (AI ops ideas)"
echo "   Blog promoter   — Mon/Wed/Fri 09:00 Amsterdam (07–08 UTC)"
echo "   Trend watcher   — every 4 hours (big AI events, max 4/week)"
echo "   Commenter       — daily ~10:00 Amsterdam (5 short replies)"
echo ""
echo "   Log: $LOG"
echo "   Test blog promo: python3 social/x_blog_promoter.py --dry-run --force"
echo "   Test trends:     python3 social/x_trend_watcher.py --dry-run"
echo "   Test comments:   python3 social/x_commenter.py --add <tweet-url> && python3 social/x_commenter.py --dry-run --force"
echo ""
echo "   ☁️  Mac-independent: push repo to GitHub + add secrets → .github/workflows/x-social.yml"
echo "   Then: bash social/disable_mac_agents.sh"