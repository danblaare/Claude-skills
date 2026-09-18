"""Add one SkillTotal scan result to the 'SkillTotal scans' table in the Obsidian skills log note.

Usage:
  python log_scan.py --component NAME --source SRC --level low|medium|high|malicious \
      --score 0-100 --decision "installed|asked user|blocked|..." \
      [--findings "short text"] [--capabilities "network, shell"] [--note PATH]

Rules:
- Only the block between the skilltotal:scans markers is touched. Everything else in the note stays.
- If the note is not reachable, the row goes to ~/.claude/skill-backups/skilltotal-reports.md and the script says so.
- Run with PYTHONIOENCODING=utf-8 on Windows.
"""
import argparse
import datetime
import json
import os
import sys

START = "<!-- skilltotal:scans:start -->"
END = "<!-- skilltotal:scans:end -->"
HEADER = (
    "| Date | Component | Source | Risk | Score | Main findings | Capabilities | Decision |\n"
    "|---|---|---|---|---|---|---|---|\n"
)
HOME = os.path.expanduser("~")
CONFIG = os.path.join(HOME, ".claude", "skills", "skill-management", "config.json")
FALLBACK = os.path.join(HOME, ".claude", "skill-backups", "skilltotal-reports.md")


def clean(text, limit=300):
    text = " ".join(str(text or "").split()).replace("|", "/")
    return text[: limit - 1] + "…" if len(text) > limit else text


def note_path(arg):
    if arg:
        return arg
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f).get("obsidian_note")
    except Exception:
        return None


def insert_row(text, row, heading):
    if START in text and END in text:
        a = text.index(START) + len(START)
        b = text.index(END)
        block = text[a:b]
        if "|---|" not in block:
            block = "\n" + heading + "\n" + HEADER
        lines = block.rstrip("\n").split("\n")
        # keep heading + header rows (first lines up to and including the |---| row), insert new row after them
        idx = max(i for i, l in enumerate(lines) if l.startswith("|---"))
        lines.insert(idx + 1, row)
        return text[:a] + "\n".join(lines) + "\n" + text[b:]
    block = f"\n{START}\n{heading}\n{HEADER}{row}\n{END}\n"
    return text.rstrip("\n") + "\n" + block


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--component", required=True)
    p.add_argument("--source", default="")
    p.add_argument("--level", required=True)
    p.add_argument("--score", default="")
    p.add_argument("--findings", default="none")
    p.add_argument("--capabilities", default="")
    p.add_argument("--decision", required=True)
    p.add_argument("--note")
    a = p.parse_args()

    row = "| " + " | ".join([
        datetime.date.today().isoformat(),
        clean(a.component, 80), clean(a.source, 120), clean(a.level, 20),
        clean(a.score, 10), clean(a.findings), clean(a.capabilities, 120), clean(a.decision, 120),
    ]) + " |"
    heading = "## SkillTotal scans (newest first)"

    target = note_path(a.note)
    if target and os.path.isdir(os.path.dirname(target)) and os.path.exists(target):
        with open(target, encoding="utf-8") as f:
            text = f.read()
        new = insert_row(text, row, heading)
        tmp = target + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        os.replace(tmp, target)
        print(json.dumps({"logged_to": target}))
        return

    os.makedirs(os.path.dirname(FALLBACK), exist_ok=True)
    text = open(FALLBACK, encoding="utf-8").read() if os.path.exists(FALLBACK) else "# SkillTotal scans\n"
    with open(FALLBACK, "w", encoding="utf-8", newline="") as f:
        f.write(insert_row(text, row, heading))
    print(json.dumps({"logged_to": FALLBACK, "warning": "Obsidian note not reachable (is the cloud drive running?)"}))


if __name__ == "__main__":
    sys.exit(main())
