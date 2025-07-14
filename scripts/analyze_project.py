#!/usr/bin/env python3
"""
📁 analyze_project.py
Walks your project directory, builds a Markdown summary of file structure and key file content,
and (optionally) sends it to GPT-4 via OpenAI API for suggestions.

Output:
    project_summary.md
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load OpenAI API key from environment or .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "project_summary.md"
SCAN_DIRS = ["src", "scripts", "docs"]  # directories to walk

def summarize_file(file_path, max_lines=20):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            content = "".join(lines[:max_lines])
            if len(lines) > max_lines:
                content += "\n... (truncated)"
            return content.strip()
    except Exception as e:
        return f"[Could not read file: {e}]"

def build_summary():
    lines = ["# 🧠 Project Summary", f"_Base directory: `{BASE_DIR.name}`_\n"]
    for subdir in SCAN_DIRS:
        full_dir = BASE_DIR / subdir
        if not full_dir.exists():
            continue
        lines.append(f"## 📂 {subdir}")
        for root, _, files in os.walk(full_dir):
            rel_root = Path(root).relative_to(BASE_DIR)
            for f in files:
                if f.endswith((".py", ".md", ".json", ".txt")):
                    f_path = Path(root) / f
                    lines.append(f"\n### 📄 `{rel_root / f}`\n```")
                    lines.append(summarize_file(f_path))
                    lines.append("```")
    return "\n".join(lines)

def save_summary(content):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Saved: {OUTPUT_FILE}")

def ask_gpt(summary_text):
    print("🤖 Asking GPT-4 for feedback...")
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": "You are a senior software architect reviewing a Python project."
            },
            {
                "role": "user",
                "content": (
                    "Here is a Markdown summary of my project structure and sample code. "
                    "Please review and suggest improvements to folder structure, file layout, and modularity:\n\n"
                    + summary_text
                ),
            },
        ],
        temperature=0.3,
    )
    reply = response.choices[0].message.content
    print("🧠 GPT-4 Suggestion:\n")
    print(reply)

if __name__ == "__main__":
    summary = build_summary()
    save_summary(summary)

    if input("🔍 Ask GPT-4 for suggestions now? (y/n): ").lower().startswith("y"):
        ask_gpt(summary)
