#!/usr/bin/env python3
"""
📄 generate_json_from_handoff.py

Reads the current handoff_latest.md file and generates a JSON summary
for use with ChatGPT or Claude.

Usage:
    python scripts/generate_json_from_handoff.py

Output:
    outputs/handoff_latest.json
"""

from pathlib import Path
import json
import re

# Define paths
base_dir = Path(__file__).resolve().parent.parent
handoff_path = base_dir / "docs" / "handoffs" / "handoff_latest.md"
output_path = base_dir / "outputs" / "handoff_latest.json"

# Parse sections into structured data
def parse_handoff_md(md_text: str) -> dict:
    sections = {}
    current_section = None
    for line in md_text.splitlines():
        header_match = re.match(r"^##\s+(.*)", line)
        if header_match:
            current_section = header_match.group(1).strip()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line.strip())
    return {k: "\n".join(v).strip() for k, v in sections.items()}

# Read and convert
if handoff_path.exists():
    raw_md = handoff_path.read_text(encoding="utf-8")
    parsed = parse_handoff_md(raw_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)
    print(f"✅ Exported: {output_path}")
else:
    print("❌ handoff_latest.md not found.")
