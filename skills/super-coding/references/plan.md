# PLAN: lock the design, then break it into small verifiable tasks

**Output:** `docs/plans/YYYY-MM-DD-<topic>.md`, approved by the owner as a plain-language summary.
Write the plan so an engineer with **zero context** could execute it: exact files, exact commands, real code for anything non-obvious. Don't write code in the project during planning.

## 1. Engineering review of the spec (before writing tasks)

**Step 0: scope challenge** (answer each explicitly):
1. What existing code, library or platform feature already solves each sub-problem? Check official docs for a built-in before planning a custom solution.
2. What is the **minimum set of changes** that meets the spec? Flag anything deferrable.
3. **Complexity smell:** 8+ files, or 2+ new services or classes, means proposing a smaller version to the owner with AskUserQuestion before continuing.
4. **Distribution:** how does the result reach users (hosting, store, package), and is that in the plan?
5. `TODOS.md`: does this plan unblock, close, or create deferred items?

Once the owner accepts or rejects a scope reduction, commit to it. Don't re-argue it later.

**Then review in this order** (at most ~8 real issues per section; decide technical issues yourself and log them as Rulings; ask only about owner-level trade-offs):

- **Architecture:** ASCII diagram of components and data flow. Dependencies point one way, with no cycles. Boring by default. Prefer reversible choices (feature flags, additive changes). For backend or system architecture, invoke `engineering:system-design` for the requirements, scale and trade-off framework.
- **Shadow paths:** for every new data flow, trace the happy path plus **nil input, empty input and upstream error**.
- **Error map:** for each failure, record what triggers it, what catches it, what the user sees, and which test covers it. Catch-all error handling is a smell. No silent failures.
- **Interaction edge cases:** double-click or double-submit, navigating away mid-action, slow or offline network, stale data, the back button, very long text, zero results, first-time vs returning user.
- **Security and privacy:** mark each task that crosses a trust boundary. Those tasks follow `security-and-hardening`.
- **Performance:** set budgets where users will feel them. Mark hot paths for `performance-optimization`.
- **Tests:** a diagram of which behaviors get unit, integration or end-to-end tests. For a new project, invoke `engineering:testing-strategy`.
- **Observability:** what will we need to see when this breaks in production (see ship.md §6)?
- **Decisions that are expensive to reverse** (database, auth provider, hosting, framework): write an ADR with `engineering:architecture` to `docs/decisions/NNNN-<title>.md`.

## 2. Map the file structure

Before writing tasks, list every file to create or modify and its single responsibility. Files that change together live together. Split by responsibility, not by technical layer. In existing code, follow the established patterns; include a split only when a file you must modify is already unwieldy.

## 3. Slice into tasks

- **Vertical slices:** each task delivers one working path through the stack ("user can create a booking"), not "build all tables" then "build all endpoints".
- **Risk first:** put the most uncertain piece (a third-party API, a tricky algorithm) early, so a failure shows up before you've built on it.
- **Contract first** when pieces could proceed in parallel: define the types and API shape as their own task.
- **Size:** XS (1 file), S (1–2), M (3–5), L (5–8; split if you can). **XL (8+ files) must be split.** Also split when a task needs more than 3 acceptance bullets, touches two independent subsystems, or has "and" in its title.
- **Batch same-shape trivia** (the same small edit across many files) into one task.
- **Checkpoint after every 2–3 tasks:** suite green, app runs, the flow is demonstrated to the owner (screenshot or local link). The owner reviews behavior, never code.

### Task template

````markdown
### Task N: <user-visible outcome>
**Files:** Create `path` · Modify `path:lines` · Test `path`
**Interfaces:** Consumes `<exact names/types from earlier tasks>` · Produces `<exact names/types later tasks rely on>`
**Acceptance:**
- [ ] <specific, testable condition>
**Steps:**
- [ ] Write failing test:
  ```ts
  <actual test code>
  ```
- [ ] Run `<exact command>` → expect FAIL (<why>)
- [ ] Implement the minimal code (<code when non-obvious>)
- [ ] Run `<exact command>` → expect PASS; run the full suite
- [ ] Save point (commit if authorized): `feat: <why>`
**Owner can check:** <what to click/see>
````

**No placeholders.** These are plan failures: "TBD", "add error handling", "handle edge cases", "write tests for the above" (without the tests), "similar to Task N" (repeat it instead), references to names no task defines, or steps that say what without showing how.

## 4. Plan header and ledger

```markdown
# <Feature> Implementation Plan
**Goal:** <one sentence>  **Spec:** docs/specs/<file>
**Architecture:** <2–3 sentences>  **Stack:** <key tech + versions>
**Execution:** inline | helper agents · commits: yes/no
## Global constraints
<exact values copied from the spec: versions, limits, naming, copy, platforms>
## Resume here
<current task · working-tree state · last verification + result · open questions>
## Ledger
- Task 1: complete (abc1234..def5678, review clean)
- Ruling: <decision> — <why> — <cost if wrong>
- Deferred (minor): <one-liner>
## Tasks
...
```

**Never overwrite a plan that still has unchecked tasks for different work.** Stop and ask; it may be mid-build in another session.

## 5. Self-review (fix inline, no need to re-review)

1. **Spec coverage:** point to a task for every spec requirement, and add tasks for any gaps.
2. **Placeholder scan** against the list above.
3. **Consistency:** names, signatures and types match across tasks (`clearLayers()` in Task 3 vs `clearAllLayers()` in Task 7 is a bug).

## 6. Owner approval: one message, plain language

- What they'll have at the end, in which order, the rough effort, and the main risks.
- What you'll need from them: accounts, API keys entered into dashboards by them, content, brand assets, decisions.
- **The execution question**, asked once with AskUserQuestion:
  - "Save progress with git commits after each working step?" (Recommended: yes. It makes every step undoable.)
  - For more than 4 tasks: "Use helper agents (faster; every task gets an independent review) or work in this session?" (Recommended: helper agents for more than 6 tasks.)

These answers are the durable authorization for commits during this plan. Pushing and deploying still need their own yes. Then go to BUILD.
