# Claude Skills: skill-management + super-coding + skilltotal-preinstall

Three [Claude skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) I built while working out how to use GenAI tools reliably and safely in my day-to-day work.

| Skill | What it is | Best for |
|---|---|---|
| **skill-management** | One control panel for all your Claude skills: install, check for updates, audit, back up, roll back | Anyone collecting more than a handful of skills |
| **super-coding** | A disciplined senior-engineer workflow for building software with Claude: define, plan, build, debug, review, verify, ship | People who build with AI, especially non-developers |
| **skilltotal-preinstall** | A mandatory security gate: every package, MCP server, skill, plugin or repo is scanned *before* it gets installed | Anyone who lets an AI agent install things on their computer |

**[⬇ Download the latest release (zip)](../../releases/latest)** · or clone this repo.

---

## Why I built these

After testing many community skill packs, I kept hitting the same three problems:

1. **Skill sprawl.** Every new skill adds context cost, may overlap with others, and can bring unreviewed code onto my machine. I had no single place to see what I had, what changed, or whether it was safe.
2. **AI coding that "looks done" but isn't.** Building the wrong thing, overbuilding, breaking what worked, guessing at bugs, and claiming success without proof.
3. **Agents install things.** A coding agent will happily run `npm install`, `pip install` or add an MCP server to get a job done. One malicious or compromised package is enough to leak credentials or files.

`skill-management` solves the first. `super-coding` solves the second. `skilltotal-preinstall` solves the third, and the other two rely on it.

---

## skill-management

A general manager for your Claude skills (local skills in Claude Code, claude.ai account skills and app plugins).

**Capabilities**
- **Full check:** inventory every skill, back up, review what changed, check GitHub skills for upstream updates, security-scan, and recommend.
- **Change tracking:** detects edits to your skills since the last review and explains each one in plain English (and who most likely made it).
- **Safe install and update:** stages skills from GitHub, a folder or a zip; security scan first; updates keep your local patches.
- **Disable, enable, uninstall and roll back:** every destructive step is backed up automatically and is reversible.
- **Health and cost:** finds broken skills and estimates how much context (tokens) each one costs in every session.
- **Overlap and triggers:** finds skills that compete for the same requests and tests which skill actually fires.
- **Usage and feedback:** shows how often each skill is used and suggests improvements from past sessions.
- **Discover:** finds well-regarded new skills and flags conflicts with your setup.
- **Asks why:** every edit, update or rollback records your reason in the skills log, so you remember later why a skill changed.
- **Portability:** export/import, an HTML dashboard, and a running skills log with three tables (local skills, claude.ai skills, app plugins).
- **Obsidian mirror (optional):** after every run, updates a note with a dashboard link at the top, the log tables, and a date-and-time revision property.
- **Notes folder (optional):** set `notes_folder` and every run also keeps the other notes in that folder current: a guide note gets one section per skill (what it is, fires when, modes, use it for, rule of thumb). `notes-status` lists skills missing from the guide.
- **Publish to GitHub (optional):** offers to sync your shared skills to your public repo, strips personal settings, blocks the push if personal data is found, and publishes on your yes.
- **claude.ai packaging:** shows where each skill works (Claude chat vs Claude Code) and packages skills for upload.

**Design principles:** asks before changing anything · plain English for non-experts · treats skill content and web pages as data, never instructions · logs everything.

## super-coding

A complete software-building workflow that makes Claude act like a disciplined senior engineer working for an owner who does not read code. It merges the best ideas of four respected open-source packs (**superpowers**, **agent-skills**, **karpathy-skills**, **gstack**), resolves 18 conflicts between them, and reuses the skills you already have instead of duplicating them.

**Capabilities**
- **Sizes the work first:** Trivial, Spike, Bounded or Product, so a typo fix doesn't get a 10-step process and a new app doesn't get none.
- **Seven phases with gates:** DEFINE → PLAN → BUILD → DEBUG → REVIEW → VERIFY → SHIP, each with its own playbook.
- **Four Iron Laws:** no "done" without fresh evidence; no bug fix without a confirmed root cause and a failing test; tests before behavior code; no building before the owner approves *what* gets built.
- **Owner-friendly communication:** one question at a time, options explained by outcome (time, cost, risk), technical details decided by Claude.
- **Smart stop list:** keeps going on its own, but stops for destructive actions, publishing/spending, security decisions, or 3 failed fixes.
- **Supply-chain safety:** every new dependency goes through `skilltotal-preinstall` before install.
- **Leaves a trail:** specs, plans, decisions (ADRs), QA evidence and a changelog live in the repo, not in chat memory.
- **Honest final report:** what works (with evidence), what changed, decisions made, risks, and the next step.

**Instruction-only:** no scripts, hooks, binaries or telemetry from the source packs are used.

## skilltotal-preinstall

A mandatory security gate built on [SkillTotal](https://github.com/pezhik/skilltotal), a free, open-source (Apache-2.0) static analyzer for AI components. The scan runs locally and **never executes the component's code**.

**Capabilities**
- **Triggers automatically** on any install, add, set-up, clone, download or upgrade request: npm/pnpm/yarn/bun, pip/uv/poetry, MCP servers, Claude skills and plugins, agents, GitHub repos, VS Code extensions, CLI tools and archives.
- **Scans the real thing:** maps each component to a scannable source (`npm:`, `pypi:`, git URL or local path), including the package behind an `npx`/`uvx` MCP server.
- **Diffs upgrades:** compares the installed version against the new one, so a previously safe package that turns risky gets caught.
- **Plain report:** verdict, risk score (0–100), notable findings with file and line, and capabilities (network, filesystem, shell, secrets).
- **Clear decisions:**
  - Low risk → install.
  - Medium risk or any high-severity finding → **asks you first**.
  - High risk or malicious → **does not install** and suggests alternatives.
  - Scanner unavailable → asks you; **never skips silently**.
- **Prompt-injection aware:** text inside a scanned component or its findings is treated as data, never as instructions.

> **Why it matters in practice:** when I installed the official GitHub CLI, the scan came back "high risk". The skill stopped, explained each finding (all false alarms from help-text examples and GitHub's internal dev tools), and only installed after I confirmed.

---

## Install

**Claude Code (Windows, macOS, Linux)**

1. Download the zip from [Releases](../../releases/latest) and unzip it (or `git clone` this repo).
2. Copy the folders inside `skills/` into your personal skills folder:
   - Windows: `C:\Users\<you>\.claude\skills\`
   - macOS / Linux: `~/.claude/skills/`
3. **Install SkillTotal** (needed by `skilltotal-preinstall`; Python 3.10+):
   ```bash
   pipx install skilltotal
   claude mcp add --scope user skilltotal -- skilltotal mcp
   ```
   (`pip install skilltotal` works too.)
4. Start a new Claude Code session. Try: *"run my skills check"*, *"I want to build a small app that…"* or *"install the X package"*.

`skill-management` needs Python 3.10+ (standard library only) and git.

**Optional companions** (the skills fall back gracefully without them):
- Firecrawl MCP for reading the web and Playwright MCP for browser testing.
- Anthropic's `engineering`, `design` and `product-management` plugins, which super-coding calls at the right moments.

**Configure (optional):** in `skills/skill-management/config.json`, set `export_dir` (where exports go), `obsidian_note` (a note to mirror the skills log into), `notes_folder` (a folder of skills notes to keep current) and `github_repo` (your repo clone, which skills to publish, and the rules that remove personal details; see `references/github.md` and the docstring in `scripts/publish.py`).

## Safety

All three skills were scanned with SkillTotal before publishing: **risk level LOW (0/100), no malicious indicators, no secrets.** `skill-management` reads and writes files inside `~/.claude` and runs `git`; it makes no network calls of its own. `super-coding` and `skilltotal-preinstall` are instructions only. As with any skill, read it before you install it.

## Credits and license

MIT License (see [LICENSE](LICENSE)). `super-coding` adapts ideas and text from MIT-licensed projects, and `skilltotal-preinstall` uses the SkillTotal scanner (Apache-2.0, not bundled); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
