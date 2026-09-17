# claude.ai: where skills live, packaging, and editing account skills

## Where each skill works
Run `where` (or read the "Claude chat" and "Claude Code" columns in `log show` or the dashboard).
- **Local skills** (`~/.claude/skills`): Claude Code on this computer only.
- **claude.ai account skills** (yours and Anthropic's): Claude chat, and synced into Claude Code.
- **Claude app plugins:** chat, Cowork and Code sessions in the app.

The claude.ai list comes from the desktop app's local copy. It is stale until the app syncs, so give its date.

`sync-remote` logs changes on the account side: skills added, updated, switched off or removed, and plugins updated. Run it at the start of every mode (shared rule 1).

## Package a local skill for claude.ai
1. Run `package --name <skill>`. It checks claude.ai's rules and builds a zip in the run folder, with a copy in `<export_dir>/claude.ai packages/`.
   - **Blockers** (the upload would fail): a name with reserved words ("anthropic", "claude") or bad characters, a description over 1024 characters or containing XML/HTML tags.
   - **Auto-fixes:** frontmatter keys claude.ai doesn't allow are moved under `metadata` in the packaged copy only.
   - **Warnings** (it would behave differently in chat): MCP tools needing connectors, local file paths, scripts or command-line tools, Claude Code-only tools and features.
2. Explain the verdict in plain English: **ready**, **works with limits** (say what won't work in chat), or **blocked** (say what to fix, and offer to fix it via `references/create-edit.md`).
3. Tell the user how to upload:
   - In claude.ai, open Settings → Capabilities (Skills), upload the zip, and turn it on.
   - If the skill already exists there, replace it or delete the old one first.
4. **After the upload** (next time the app syncs), `where` shows the skill as uploaded. If both the local copy and the claude.ai copy are active, Claude Code loads it twice.
   - Recommend disabling the local copy (`references/remove.md`) with the reason "uploaded to claude.ai".
   - Keep the local copy only if the user wants Code-only differences.

## Edit a claude.ai account skill
The app's copy is overwritten on every sync, so never edit it directly.
1. Run `pull-claude-ai --name <skill>`. This creates an editable copy in `~/.claude/skill-backups/claude-ai-sources/<skill>/` and keeps the untouched original under `_original/`. Pass `--replace` only after confirming; the previous editable copy is archived.
2. Make the edits in the editable copy, following `references/create-edit.md` (plain-English before/after, approval, `validate --path <copy>`).
3. Ask the user for the rationale (shared rule 4), then log it: `log event --skill claude.ai:<skill> --type modified --by Claude --summary "<what changes for the user>; waiting for re-upload" --rationale "<their reason>"`.
4. Run `package --name <skill>`; it picks up the editable copy. Give the upload steps above.
5. After the user re-uploads, `sync-remote` records "Updated in claude.ai".

## Refreshing bundled guidelines (e.g. prompt-optimizer's model guides)
When a skill bundles time-sensitive references with a "Sources" list (such as `references/model-guides.md`):
1. Fetch those pages with Firecrawl.
2. Compare them with the bundled files and summarise what changed in plain terms.
3. On approval, update the editable copy, then log, package and ask the user to re-upload.

Offer this during a full check when a bundled "as of" date is more than 60 days old.
