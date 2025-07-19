#!/bin/bash

# 📄 save_handoff.sh
# This script snapshots the current handoff_latest.md file,
# stages it and the new snapshot, commits both to Git,
# and generates a JSON export for Claude or ChatGPT.

# Define directories and script location
HANDOFF_DIR="docs/handoffs"
SCRIPT_PATH="src/utils/snapshot_handoff.py"
LATEST="$HANDOFF_DIR/handoff_latest.md"
JSON_SCRIPT="scripts/generate_json_from_handoff.py"

# Step 1: Run snapshot script
echo "🕒 Creating snapshot..."
python "$SCRIPT_PATH"

# Step 2: Identify most recent snapshot file
SNAPSHOT=$(ls -t $HANDOFF_DIR/claude_handoff_*.md | head -n1)

# Step 3: Stage files for commit
echo "📁 Staging files..."
git add "$LATEST"
git add "$SNAPSHOT"

# Step 4: Commit with a timestamped message
NOW=$(date "+%Y-%m-%d %H:%M")
echo "✅ Committing changes..."
git commit -m "📄 Saved handoff snapshot @ $NOW"

# Step 5: Generate JSON export for Claude/ChatGPT
echo "🧠 Generating JSON export..."
python "$JSON_SCRIPT"

echo "🎉 Handoff saved, committed, and exported!"
