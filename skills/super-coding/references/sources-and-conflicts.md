# Sources, merge decisions and overlap map

## Sources (all MIT-licensed; ideas and text adapted, no code executed or copied in)

| Pack | Repo | Commit reviewed (2026-09-17) | SkillTotal |
|---|---|---|---|
| superpowers (Jesse Vincent) | github.com/obra/superpowers | b36e0829 | low (20/100) |
| agent-skills (Addy Osmani) | github.com/addyosmani/agent-skills | be4e44a9 | low (0/100) |
| karpathy-skills (forrestchang) | github.com/forrestchang/andrej-karpathy-skills | 2c606141 | low (0/100) |
| gstack (Garry Tan) | github.com/garrytan/gstack | a6b3a575 | critical (100/100): mostly doc false positives, but it ships real executables (browser daemon, `curl \| bash` installers, `-ExecutionPolicy Bypass`, a script that reads `~/.claude/.credentials.json`) |

This skill is **instruction-only**. None of the packs' scripts, hooks, binaries or telemetry are used.

## What came from where

| Area | Taken from |
|---|---|
| Operating principles | karpathy (think first, simplicity, surgical, goal-driven) · agent-skills core behaviors · gstack ethos (search before building, user sovereignty, completeness) |
| Tiers and approval gate | superpowers brainstorming (spike/bounded/architectural, heavier-when-unsure ratchet) + a Trivial tier from karpathy's "use judgment" |
| DEFINE | agent-skills interview-me (hypothesis + confidence + guess), idea-refine, spec-driven (six areas, capability map) · gstack office-hours (six forcing questions, premises, mandatory alternatives), plan-ceo-review (scope modes) |
| PLAN | superpowers writing-plans (no placeholders, interfaces, self-review) · agent-skills planning (vertical slices, sizing, checkpoints) · gstack plan-eng-review (complexity smell, shadow paths, error map, test diagram) |
| BUILD | agent-skills incremental, TDD, source-driven, context-engineering, doubt-driven, constraint-driven (quality floor) · superpowers TDD iron law, subagent-driven development, parallel agents, worktrees · gstack reuse ladder |
| DEBUG | superpowers systematic-debugging (4 phases, 3-fix rule) · gstack investigate (scope lock, pattern table, 3-hypothesis stop, blast radius) · agent-skills debugging |
| REVIEW | agent-skills five-axis review, simplification, dependency discipline · gstack review checklist (critical pass, fix-first, suppressions) · superpowers receiving and requesting code review |
| VERIFY | superpowers verification-before-completion · agent-skills definition of done · gstack qa (modes, health score, fix loop, self-regulation) |
| SHIP | superpowers finishing-a-branch · agent-skills git workflow, CI/CD, shipping-and-launch, observability, documentation · gstack ship, land-and-deploy, canary, document-release, retro, setup-deploy |
| UI / backend | agent-skills frontend-ui, api-design, deprecation-and-migration · gstack plan-design-review, design-review (principles, slop list) |

## Conflicts resolved

| # | Conflict | Resolution |
|---|---|---|
| 1 | gstack "Boil the Ocean" vs karpathy/superpowers "simplicity / YAGNI" | They measure different things. **Completeness pushes coverage up** (tests, edge cases, error/empty states for the requested scope). **Simplicity pushes unrequested structure down** (features, abstractions, config). Expansions are only ever offered as opt-in choices. |
| 2 | superpowers "approval for every task" vs gstack "never ask trivial confirmations" vs karpathy "use judgment for trivial" | Tiered: Trivial = no gate; Spike = a nod; Bounded and Product = explicit approval of **what** gets built. Mechanical steps never ask. |
| 3 | agent-skills "human reviews every phase" vs a non-technical owner | The owner approves **what and why** in plain language and sees demos; Claude plus fresh-context reviewer agents approve **how** (the code). |
| 4 | superpowers "execute continuously" vs agent-skills "checkpoint with human after 2–3 tasks" | Execute continuously and stop only for the named stop list; checkpoints are behavior demos, not code reviews. |
| 5 | superpowers strict TDD ("delete code written before tests") vs UI, config, spikes | TDD scope table in build.md: strict for logic, data and bug fixes; behavior tests for UI; visual or boot verification for styling and config; spikes are throwaway. |
| 6 | Three debugging workflows + `engineering:debug` | One protocol (debug.md). `engineering:debug` is called for its frame and report; the stricter iron-law rules apply on top. |
| 7 | Three review styles + built-in `code-review` + `engineering:code-review` | Built-in `code-review` does the diff pass; review.md adds the critical checklist, quality floor and fix-first. Fix-first splits into auto-fix, decide-and-log (technical) and ask-owner (user-visible, money, risk). |
| 8 | gstack cross-model review (Codex CLI) and agent-skills doubt via Gemini/Codex CLIs | Not installed. A fresh-context adversarial subagent (prompts.md) replaces them. |
| 9 | Browsers: gstack's own daemon and "never use Chrome MCP" · agent-skills Chrome DevTools MCP | Default: **Playwright MCP**, falling back to the built-in browser. |
| 10 | Web research: gstack Aside/WebSearch · agent-skills Context7 | Default: **Firecrawl** (`firecrawl-web-reading`), falling back to WebFetch/WebSearch. |
| 11 | Artifact locations (`docs/superpowers/*`, `SPEC.md` + `tasks/`, `~/.gstack/projects`) | One in-repo layout (SKILL.md §7); a project's existing conventions win. |
| 12 | Worktree by default (superpowers) vs branches | A feature branch by default; worktrees only for parallel streams, via the native `EnterWorktree` tool. |
| 13 | gstack 4-digit VERSION and a queue-aware bump tool vs semver | Semver + git tags + a human-written CHANGELOG. |
| 14 | Harness rule "commit only when the user asks" vs incremental save-point commits | Asked once at plan approval, and that answer authorizes commits for the plan. Pushes and deploys always need their own yes. |
| 15 | superpowers "1% chance → must invoke" meta-skill and the prompt-optimizer hook | Not adopted: the description handles triggering. The prompt-optimizer's brief feeds DEFINE §0 so questions aren't asked twice. |
| 16 | gstack one-question-per-expansion ceremonies (15–30 questions) | Capped: at most 4 expansion candidates in one multiSelect question. |
| 17 | gstack `/careful` and `/freeze` hooks | The behavior is kept as rules (the §6 stop list, the debug scope lock). If hard enforcement is wanted, add hooks via `update-config`, only if the owner asks. |
| 18 | New dependencies: every pack installs freely | Every install goes through `skilltotal-preinstall` (a mandatory safety gate; if it isn't installed, review the package manually and say so). |

## Overlap map with the existing setup

| Existing skill | How super-coding uses it |
|---|---|
| `security-and-hardening`, `performance-optimization` (local, from agent-skills) | **Called**, never duplicated |
| `firecrawl-web-reading` / `apify-structured-scraping` | Firecrawl called for docs and landscape research; Apify only if a product needs scraped data |
| `skilltotal-preinstall` | Called before every package or CLI install |
| `skill-management` | Unrelated (manages skills); excluded in the description |
| Built-ins `code-review`, `simplify`, `security-review`, `run`, `init`, `claude-api`, `loop` | Called at their points in REVIEW / VERIFY / BUILD / SHIP |
| `engineering:debug`, `:system-design`, `:architecture`, `:testing-strategy`, `:deploy-checklist`, `:documentation`, `:tech-debt`, `:incident-response` | Called (they provide the frame or template; super-coding adds the gates) |
| `engineering:code-review` | **Superseded** by built-in `code-review` + review.md (same job, less depth). Not called. |
| `engineering:standup` | Not coding work; left alone |
| `design:design-system`, `:accessibility-review`, `:design-critique`, `:ux-copy` | Called in the frontend and verify phases |
| `design:design-handoff`, `:user-research`, `:research-synthesis` | Not called (designer-to-developer handoff and research, outside the build loop) |
| `product-management:product-brainstorming`, `:write-spec` | Called in DEFINE (divergent ideas; product half of the spec) |
| `product-management:brainstorm` | **Overlaps** with `product-brainstorming`; super-coding calls only `product-brainstorming` |
| `legal:compliance-check` | Called at SHIP for personal data or payments |
| `miro:miro-code-review`, `:miro-code-spec`, `:miro-code-explain-on-board` | Only when the owner wants the review, spec or explanation **on a Miro board** (the Miro connector needs authorization first); otherwise review.md and define.md cover them |
| `prompt-optimizer` (claude.ai, auto-run via hook) | Runs first on substantive requests; its brief is consumed in DEFINE §0, not repeated |
| `artifact-design`, `dataviz` | Used when the deliverable is an Artifact page or a chart |
| Playwright MCP | Browser QA and canary checks |

**Not adopted from the packs (and why):** gstack's browser daemon, gbrain, telemetry, Greptile, Codex, iOS, PDF, benchmark-models, plan-tune and version-queue tooling (executables, external services, or not relevant) · superpowers' visual-companion server (executable; Artifacts cover visual mockups) and writing-skills (covered by `skill-management` / `skill-creator`) · agent-skills' slash commands and persona agents (their jobs are covered by built-in skills and prompts.md).

## Maintaining this skill

- To pick up upstream improvements, compare new commits in the four repos against the commits above and port **ideas**, not scripts. Scan any new source with SkillTotal first.
- Keep SKILL.md under ~300 lines. Detail belongs in `references/`.
- When the owner adds or removes a skill, update the Calls column in SKILL.md §4 and the overlap map above.
