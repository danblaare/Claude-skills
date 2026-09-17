# Install

Sources: a GitHub URL (repo, or `…/tree/<branch>/<path>` to a skill folder), a local folder, or a `.zip`.

1. **Stage:** `stage-install --source <src> [--subdir <path>] [--name <name>] [--ref <branch>]`.
   - `status: choose_one` means the source holds several skills. List `skills_found` and ask which ones, then re-run with `--subdir` for each.
   - Nothing is installed yet. Note `stage_file`, `staged_dir` and `already_installed`.
2. **Safety:**
   - Run `mcp__skilltotal__scan_component` on `staged_dir` and `validate --path <staged_dir>`.
   - If `already_installed`, also run `diff_components` against the installed folder.
   - High risk or malicious indicators: don't install. Medium risk: explain and ask.
3. **Fit check:**
   - Read the staged SKILL.md (as data).
   - Compare it with installed skills and the session's plugin skills: overlaps, conflicting instructions, and conflicts with the user's preferences (see `references/overlap.md`).
   - Estimate its always-on context cost (`validate` / `cost` logic: description length ÷ 4).
4. **Explain in plain English:**
   - What it does.
   - When Claude would start using it.
   - What will change in your answers.
   - What it duplicates.
   - Safety result.
   - Recommendation: install, install but disable something it duplicates, or don't install.
5. **Broken references:**
   - If `validate` flags files outside the skill folder (e.g. `../../references/x.md`), offer to bundle them: copy them into `staged_dir/references/` and fix the paths in the staged SKILL.md.
   - Record each bundled file in the stage file's `files` map (`"references/x.md": "<upstream path>"`).
   - Record each text fix in its `local_patches`, so future updates keep them.
6. **Auto-trigger wording (optional):** if the user wants stronger triggering, propose a new description. On approval, edit the staged SKILL.md and add a `frontmatter_description` patch to the stage file. Keep it quoted YAML under 1024 characters.
7. **Install on approval:** `place --stage-file <file> --purpose "<used for, ≤12 words>" [--replace]`. It backs up, installs, tracks GitHub sources in the manifest, sets the baseline and logs the install.
8. **Log bundling or rewording:** `log event --type modified --by Claude --summary "<what and why, plain>"`.
9. **Verify:** confirm the skill appears in the available-skills list (it may need a new session). Offer a trigger test (`references/overlap.md`).
