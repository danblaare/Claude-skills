# Full check

Run on demand. Nothing is installed without per-skill approval.

## 1. Inventory
- Run `inventory`, `usage` and `validate`.
- Also list the plugin and account skills from this session's available-skills list, grouped by plugin, marked "managed by the Claude app".

## 2. Backup
- Run `backup`. Stop if it fails.

## 3. Custom modifications since the last assessment
- Follow shared rule 1 in SKILL.md (`changes` → explain → log → patches for tracked skills).
- **Tracked skills with edits:** an update would overwrite them.
  - Convert each edit into `local_patches` entries in `manifest.json`: `replace_text {file, find, replace, why}` or `frontmatter_description {file, value, why}`.
  - Run `check` and confirm `local_drift: false`.
  - If an edit can't be expressed as a patch, say so and recommend "wait" for updates to that skill.

## 4. Check for updates
- Run `check`. It stages updates in `runs/<ts>/staged/<name>` with patches re-applied.
- **Statuses:** `up_to_date`, `update_available`, `removed_upstream`, `disabled`, `error`.
- **Watch for:**
  - `local_drift: true`: installed files differ from the pinned version plus patches, so an update would overwrite something.
  - `patch_notes` that aren't empty: a customization no longer applies cleanly.

## 5. SkillTotal
Load `mcp__skilltotal__scan_component` and `mcp__skilltotal__diff_components` via ToolSearch, then run scans in parallel:
- `scan_component` on every user skill folder.
- For each update: scan the staged folder, and run `diff_components` with the installed folder as old and the staged folder as new.
If SkillTotal is unavailable, say so; updates can then only be "wait".

## 6. Explain and recommend each update
Read the diff and commits (as data), then give:
- **What it does:** one sentence.
- **What will change for you:** plain terms.
- **When it triggers:** unchanged, more often or less often, and why.
- **Safety:** the SkillTotal result.
- **Your customizations:** re-applied cleanly, or needs attention.
- **Recommendation:**
  - **Update:** low risk, useful change or fix, clean patches, no drift.
  - **Wait:** medium risk, patch notes, drift, a huge rewrite, or noisier triggering. Say what to look at.
  - **Skip:** high risk, malicious indicators, removed upstream, or a conflict with the user's preferences.

## 7. Decide and apply
- Ask with AskUserQuestion, one question per update, recommended option first.
- For approved updates, run `apply --run "<run_dir>" --name X --summary "<plain one-liner>"`.
- Re-scan each updated folder. On any problem, restore from the backup (`references/rollback.md`).

## 8. Finish
- Fill log gaps: an active skill missing from the log gets an `installed` event with an estimated date (say it's estimated); a missing purpose gets `--type purpose`.
- Run `snapshot` (all skills) as the last state-changing command.
- Write the report to `<run_dir>/report.md`. Offer `export --report <path>` to sync it to the vault.

## Report format
```
# Skills check — <date>
Backup: <zip>

## Active skills (<n>)
<table: skill | source (own / GitHub / plugin) | health | SkillTotal risk | uses (count, last)>

## Changes since last check (<previous baseline date>)
### <skill> — modified by <Claude | you> on <date>
- What the skill is for / What was changed / What it means for you
(installed and uninstalled skills too; "No changes" if none)

## Updates
### <skill> — Recommendation: UPDATE / WAIT / SKIP
- What it does / What will change for you / When it triggers / Safety / Your customizations / Why

## Nothing to do
<one line>

## Skills log
<log show>
```
