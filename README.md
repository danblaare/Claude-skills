# Claude Skills: skill-management + super-coding

Two [Claude skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) I built while working out how to use GenAI tools reliably in my day-to-day work.

| Skill | What it is | Best for |
|---|---|---|
| **skill-management** | One control panel for all your Claude skills: install, check for updates, audit, back up, roll back | Anyone collecting more than a handful of skills |
| **super-coding** | A disciplined senior-engineer workflow for building software with Claude: define, plan, build, debug, review, verify, ship | People who build with AI, especially non-developers |

**[⬇ Download the latest release (zip)](../../releases/latest)** · or clone this repo.

---

## Why I built these

After testing many community skill packs, I kept hitting the same two problems:

1. **Skill sprawl.** Every new skill adds context cost, may overlap with others, and can bring unreviewed code onto my machine. I had no single place to see what I had, what changed, or whether it was safe.
2. **AI coding that "looks done" but isn't.** Building the wrong thing, overbuilding, breaking what worked, guessing at bugs, and claiming success without proof.

`skill-management` solves the first. `super-coding` solves the second.

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
- **Portability:** export/import, an HTML dashboard, a running skills log, and an optional Obsidian note mirror.
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
- **Supply-chain safety:** every new dependency is security-scanned before install.
- **Leaves a trail:** specs, plans, decisions (ADRs), QA evidence and a changelog live in the repo, not in chat memory.
- **Honest final report:** what works (with evidence), what changed, decisions made, risks, and the next step.

**Instruction-only:** no scripts, hooks, binaries or telemetry from the source packs are used.

---

## Install

**Claude Code (Windows, macOS, Linux)**

1. Download the zip from [Releases](../../releases/latest) and unzip it (or `git clone` this repo).
2. Copy the folders inside `skills/` into your personal skills folder:
   - Windows: `C:\Users\<you>\.claude\skills\`
   - macOS / Linux: `~/.claude/skills/`
3. Start a new Claude Code session. Try: *"run my skills check"* or *"I want to build a small app that…"*.

`skill-management` needs Python 3.10+ (standard library only) and git.

**Optional companions** (the skills fall back gracefully without them):
- A security scanner for components, e.g. the SkillTotal MCP server.
- Firecrawl MCP for reading the web and Playwright MCP for browser testing.
- Anthropic's `engineering`, `design` and `product-management` plugins, which super-coding calls at the right moments.

**Configure (optional):** in `skills/skill-management/config.json`, set `export_dir` (where exports go) and `obsidian_note` (a note to mirror the skills log into).

## Safety

Both skills were scanned with SkillTotal before publishing: **risk level LOW (0/100), no malicious indicators, no secrets.** `skill-management` reads and writes files inside `~/.claude` and runs `git`; it makes no network calls of its own. As with any skill, read it before you install it.

## Credits and license

MIT License (see [LICENSE](LICENSE)). `super-coding` adapts ideas and text from MIT-licensed projects; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
