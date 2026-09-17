# Dashboard

1. **Build:** run `dashboard`. It writes `~/.claude/skill-backups/dashboard.html` from live data: status of every skill (active / disabled / uninstalled), health issues, update status from the last check, usage, context cost, source, and a history timeline from the log.
2. **Show it:**
   - **Local:** give the file link. `export` also copies it to the vault folder.
   - **Online (optional, ask the first time):** publish it as a private Artifact so it opens on any device.
     - First publish: load the `artifact-design` skill, then call the Artifact tool with `file_path` = the dashboard file, `favicon` "🧰" and a one-sentence `description`. Save the returned URL as `dashboard_artifact_url` in `config.json`.
     - Later: publish the regenerated file with `url` = the saved URL, so the link stays the same.
3. **Summarise in chat:** 3–5 lines on what needs attention (errors, updates waiting, unused or overlapping skills), with the modes that fix them.
