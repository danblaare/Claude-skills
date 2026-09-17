# Health and cost

## Health check
Run `validate`. It checks every user skill for:
- **Errors:** missing SKILL.md, frontmatter that doesn't parse, no name or description, or a description over 1024 characters. These skills silently fail to load or trigger.
- **Warnings:** name/folder mismatch, references to files that don't exist, non-UTF-8 files.
- **Notes:** description doesn't say when to use it, SKILL.md over 500 lines, cache folders, unrecognised frontmatter keys.
- **Cross-checks:** manifest entries without a skill, skills missing from the log, log status not matching the folders.

Report errors first, in plain English: what's wrong, what the user notices (e.g. "Claude will never pick this skill up"), and the fix. Offer to fix each one. Edits follow `references/create-edit.md`, so they're logged and, for tracked skills, patched.

## Cost report
Run `cost`. Explain:
- **Always-on tokens:** name plus description, loaded into every session whether used or not. This is the real ongoing cost.
- **On-use tokens:** the full SKILL.md, loaded when the skill starts.
- **Reference tokens:** extra files, loaded only if the skill reads them.

Add plugin skills from the session's available-skills list: estimate description length ÷ 4.

Show the top consumers and the total always-on figure. Give context: a few thousand always-on tokens is modest; it matters when many overlapping skills pile up.

Suggest savings only when they're real:
- Shorten bloated descriptions.
- Move long SKILL.md detail into references.
- Disable unused skills (`references/feedback.md`) or duplicates (`references/overlap.md`).
