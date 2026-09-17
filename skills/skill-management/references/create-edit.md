# Create or edit a skill

Covers the user's own skills and third-party ones.

## Create
1. **Interview first.** Use AskUserQuestion or short questions:
   - What should it do?
   - When should it start (automatically on certain topics, or only when asked)?
   - What output should it produce?
   - Which tools or connectors should it use, and what must it never do?
2. **Check it isn't redundant.** Look for existing user and plugin skills that already cover this (`references/overlap.md`). Say so if one does.
3. **Scaffold:** `new --name <kebab-name> --description "<draft>" --purpose "<used for>"`. This creates the SKILL.md, sets the baseline and logs the install.
4. **Write the body.** Keep SKILL.md short (under ~300 lines). Put long detail in `references/*.md` and deterministic steps in `scripts/`. The description must:
   - Say what it does and when to use it (`Use when…`; use `Use AUTOMATICALLY (without being asked) whenever…` for proactive skills, or `Use ONLY when the user explicitly asks…` for manual ones).
   - Be quoted YAML under 1024 characters.
5. **Check:** `validate --name <name>`, then offer a trigger test with 2–3 prompts that should start it and 1–2 that shouldn't.
6. **Finish:**
   - Ask the user why they want the skill (shared rule 4). Log the body writing: `log event --type modified --by Claude --summary "<plain>" --rationale "<their reason>"`.
   - Run `snapshot --name <name>`.

## Edit
1. Read the current SKILL.md (and references). Restate what the skill does today in plain English.
2. Propose the edit as a before/after of the changed lines, plus what it means in practice ("Claude will now…"). Apply only after a yes.
3. **Tracked GitHub skill** (in `manifest.json`): add the edit to its `local_patches` (`replace_text` or `frontmatter_description`, with a `why`). Run `check` and confirm `local_drift: false`.
4. **Finish:**
   - Run `validate --name <name>`.
   - Ask the user for the rationale (shared rule 4).
   - Log it: `log event --type modified --by Claude --summary "<what changed and its effect>" --rationale "<their reason>"`.
   - Run `snapshot --name <name>`.
5. If the edit changes triggering, offer a trigger test.

Writing guidance: `anthropic-skills:skill-creator` holds detailed skill-authoring advice. Invoke it for complex skills.
