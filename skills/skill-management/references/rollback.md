# Rollback

1. **List restore points:** run `backups`. It shows full backups (`skills-*.zip`), safety backups taken before restores, uninstall archives, and exports in the sync folder. Show them as a short table: date, type, skills included.
2. **Pick:** the user chooses the point and the skills. Default to the skill they named; restore everything only if asked.
3. **Preview:** `restore --backup <zip> --name <skills…> --preview`. For each skill, read the diff file and explain plainly what would change back: "The description goes back to the older wording, so Claude will use it less often". Skip skills that are `identical`.
4. **SkillTotal:** if the zip came from outside `~/.claude/skill-backups` (e.g. an export from another machine), scan the extracted folders first.
5. **Restore on approval:** `restore --backup <zip> --name <skills…> --reason "<why>"`. It takes a safety backup first, replaces the folders, logs a "restored" event and refreshes those skills' baseline.
6. **Tracked GitHub skills:** a restored older version makes the next `check` show an update. Say so. Its manifest commit is unchanged; if the user wants to stay on the old version, advise "skip" on that update.
7. **Undo a restore:** use the `skills-before-restore-*.zip` it created.
