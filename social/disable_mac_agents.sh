#!/usr/bin/env bash
# Stop local Mac launchd agents once GitHub Actions is your primary runner.
set -euo pipefail
UID_NUM="$(id -u)"
for label in com.murmur.red.xscheduler com.murmur.red.blogpromoter com.murmur.red.trendwatcher; do
    launchctl bootout "gui/$UID_NUM/$label" 2>/dev/null || true
    rm -f "$HOME/Library/LaunchAgents/${label}.plist"
    echo "Stopped $label"
done
echo "Mac agents off. GitHub Actions (.github/workflows/x-social.yml) is now primary."