#!/usr/bin/env bash
# One-time installer: deps + launchd daemon for hands-free X posting.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-$(command -v python3)}"
PLIST_SRC="$ROOT/social/com.murmur.red.xscheduler.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.murmur.red.xscheduler.plist"
LOG="$ROOT/social/post.log"

echo "▸ Redirecting to full X automation installer..."
exec bash "$ROOT/social/install_x_automation.sh"