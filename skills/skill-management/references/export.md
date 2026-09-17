# Export and sync

The sync folder is `export_dir` in `config.json` (for example a folder in an Obsidian vault or a cloud drive). If it isn't set, ask the user where to export and save the answer in `config.json`.

## Export
Run `export [--report <run_dir>/report.md]`. It writes:
- `exports/skills-export-<timestamp>.zip`: all user skills, disabled skills and the log (newest `keep_exports` kept).
- `Skills log.md`: an Obsidian note with the log table.
- `Skills dashboard.html`: the dashboard.
- `Reports/<date> skills report.md`: when a report is passed.
- The skills log note set in `obsidian_note`, if configured: its dashboard link (top of the note) and log section are refreshed, and its revision property is set to the current date and time. This also happens at the end of every run (shared rule 9).

Export after any run that changed skills, and offer it at the end of a full check. If the folder isn't reachable (for example a cloud drive that isn't running), say so and skip. Never write elsewhere without asking.

## Restore on this or another machine
1. **Pick a zip:** from `<export_dir>/exports/`; the `backups` command lists them.
2. **Restore skills:** follow `references/rollback.md` with that zip. It holds `skills/<name>/…`, so restore works directly, and SkillTotal scans run first because it comes from outside.
3. **Merge history:** `import-log --zip <zip>` merges the exported log into the local one; events are de-duplicated.
4. **Disabled skills:** these are stored under `disabled/` in the zip. Restore them only if asked, by copying them into `~/.claude/skill-backups/disabled/`.
5. **Rebuild the baseline:** run `snapshot` afterwards so the imported state isn't reported as modifications.

## Changing the folder or note
Edit `export_dir` or `obsidian_note` in `config.json` on request, then confirm the new location exists.
