# Skills notes folder

`notes_folder` in `config.json` is the Obsidian folder that holds the notes about the user's skills. Keep every note in it current. Act by yourself. Do not ask first, except for verdicts (see below).

## Notes and owners

| Note | Kind | How to update |
|---|---|---|
| `00_Skills Log.md` | Machine-written | The `obsidian-note` command does it, every run. Do not edit by hand. |
| `00_Skills explained.md` | Hand-written guide: what each skill does, modes, trigger words, verdict | You edit it, as below. |
| `00_Currently installed tools and MCPs.md` | Hand-written list of tools and MCP servers (not skills) | You edit it when an MCP server or tool is installed or removed. |
| Any other note | Not managed | Leave it alone. Do not create notes. |

## Steps in every run that changed something
1. Run `notes-status`. It lists installed skills missing from `00_Skills explained.md`, skills the note names that are gone, and each note's revision date.
2. Copy each note to `~/.claude/skill-backups/notes/<name>-<timestamp>.md` before you edit it.
3. Edit `00_Skills explained.md`:
   - **Installed or created skill:** add a section in the right group. Every section must have all five fields, in this order, each as its own paragraph:
     1. **What it is:** one or two plain sentences.
     2. **Fires when:** the trigger words and the slash command, taken from the skill's own description.
     3. **Modes:** the variants, sub-commands or levels, or "none".
     4. **Use it for:** two or three concrete example requests.
     5. **Rule of thumb:** one short sentence that helps the user decide when to use it.
     Never add a section with a field missing. If the skill's description does not give enough to fill a field, read its `SKILL.md`. If that is not enough, write "Not checked" for that field and say so in the final answer.
   - **Edited skill:** rewrite only the fields that changed (what it is, fires when, modes, use it for, rule of thumb).
   - **Uninstalled skill:** remove its section and its row entry.
   - **Disabled or enabled skill:** mark it in its section. Keep the section.
   - Update the counts in the verdict table at the top.
   - Do not change a verdict (keep, turn off) unless the user asks. Put a proposed verdict in your answer instead.
4. Edit `00_Currently installed tools and MCPs.md` only for tool or MCP changes. Add or remove its section. Keep the note's wording style.
5. Set the note's revision property (`last-revision`) to `YYYY-MM-DDTHH:MM` on every note you changed.
6. Use Python for edits inside a large note (the Obsidian edit tool cannot edit the middle of a note). Count the sections before and after.
7. Before you finish, run `notes-status`. It must list no missing skills, and every skill section must have the five fields. Fix any gap in the same run.
8. In the final answer, list each note changed and one line per change.

## Rules
- Write documents in Simplified Technical English (the `ste` skill): short sentences, every acronym expanded at first use.
- Keep the user's tags, wikilinks and callouts.
- If the folder is not reachable, say so and write nowhere else.
