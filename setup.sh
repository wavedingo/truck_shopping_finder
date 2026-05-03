#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(which python3)"
PLIST_NAME="com.truckfinder.daily"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

# Substitute placeholders with actual paths
sed -e "s|__PYTHON__|$PYTHON|g" \
    -e "s|__PROJECT_DIR__|$SCRIPT_DIR|g" \
    "$PLIST_SRC" > "$PLIST_DEST"

# Unload any existing version first
launchctl unload "$PLIST_DEST" 2>/dev/null || true

# Load the job
launchctl load "$PLIST_DEST"

echo ""
echo "Scheduled: truck finder will run daily at 7:00 AM"
echo "Python:    $PYTHON"
echo "Project:   $SCRIPT_DIR"
echo ""
echo "Verify:    launchctl list | grep truckfinder"
echo "Uninstall: launchctl unload $PLIST_DEST && rm $PLIST_DEST"
