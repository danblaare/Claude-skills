# Disable, enable, uninstall

Plugin skills can't be removed here; tell the user to manage them in the Claude app's plugin settings.

## Choose
Explain the difference plainly:
- **Disable** (recommended when unsure): the skill moves to `~/.claude/skill-backups/disabled/` and Claude stops using it in new sessions. `enable` brings it back unchanged.
- **Uninstall:** the folder is deleted. An archive copy is kept in `~/.claude/skill-backups/uninstalled/` and a full backup is taken first. It stops being tracked for updates.

Before acting, say what the user loses: what the skill did, and which other skill (if any) covers it. Use `usage` for when it was last used.

## Run
- `disable --name X --reason "<user's reason>"`
- `enable --name X`
- `uninstall --name X --reason "<user's reason>"`

Ask for a reason with AskUserQuestion, including a "No reason / skip" option. The reason goes into the log.

These commands refuse unsafe cases (e.g. removing skill-management itself, or a name that isn't installed). Report the refusal plainly.

Note: changes apply to new sessions. The current session may still list the skill.
