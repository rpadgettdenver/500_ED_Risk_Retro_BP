
"""
📄 snapshot_handoff.py

Utility script to archive the current Claude session handoff (handoff_latest.md)
into a timestamped file for tracking and versioning.

Run this manually after significant updates or at the end of a working session.

Usage:
    python src/utils/snapshot_handoff.py

Output:
    Creates a file like:
    docs/handoffs/claude_handoff_20250713_1045.md
"""

from datetime import datetime
from pathlib import Path
import shutil

# Set base directory to project root (../../.. from this script)
base_dir = Path(__file__).resolve().parent.parent.parent  # back out of utils/ and src/

handoff_dir = base_dir / "docs" / "handoffs"
latest_file = handoff_dir / "handoff_latest.md"


def snapshot_latest_handoff() -> Path:
    """
    Archives handoff_latest.md to a timestamped Markdown file.

    Returns:
        Path to the newly created snapshot file, or None if source does not exist.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    archived_file = handoff_dir / f"claude_handoff_{timestamp}.md"

    if latest_file.exists():
        shutil.copy(latest_file, archived_file)
        print(f"✅ Snapshot created: {archived_file.name}")
        return archived_file
    else:
        print("❌ No handoff_latest.md found in docs/handoffs/")
        return None


if __name__ == "__main__":
    snapshot_latest_handoff()