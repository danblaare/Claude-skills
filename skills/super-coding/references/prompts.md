# Helper-agent prompt templates

Use these with the Agent tool (`subagent_type: general-purpose` unless noted). **Always set `model` explicitly.** Hand over **file paths**, never pasted history. Helpers **never spawn their own helpers**, and reviewers are **read-only**. Fill every `<…>`.

Model guide: `haiku` when the brief contains the full code (transcription plus tests) · `sonnet` for normal implementation and task reviews · `opus` for design-heavy tasks, final whole-branch reviews and doubt reviews on high-stakes code.

---

## Implementer

```
You are implementing Task <N>: <name> in <repo path>, on branch <branch>.

READ FIRST — your requirements, exact values to use verbatim: <brief file>
Where this fits: <one line>
Interfaces from earlier tasks you must use: <exact names/signatures>
Decisions already made (do not revisit): <Ruling lines relevant to this task>
Project rules: read CLAUDE.md. Global constraints: <verbatim from plan>

Before starting: if requirements, approach or dependencies are unclear, ask now (status NEEDS_CONTEXT).

Your job:
1. TDD: write the failing test, run it and confirm it fails for the right reason, write minimal code, run it green, then run the relevant suite + typecheck + lint.
2. Implement exactly the task. No extra features, no refactoring outside the task, follow existing patterns and the plan's file structure.
3. Quality floor: no suppressions, skipped tests, empty catches, stubs, or secrets.
4. Commit: <yes: "type: why" message | no: leave changes uncommitted>.
5. Self-review your own diff: requirements all met? anything extra? edge cases? tests assert real behavior? output clean?

You do not dispatch subagents, and never spawn a reviewer. Review is scheduled separately.
Stop and report BLOCKED if the task needs an architectural decision with several valid options, you can't understand needed code after focused reading, or the plan seems wrong. Bad work is worse than no work.

Write the full report to <report file>: what you built, TDD evidence (RED command + failing output + why expected; GREEN command + passing output), files changed, self-review findings, concerns.
Reply ONLY with (under 15 lines): Status DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED · commits (sha + subject) · one-line test summary · concerns · report path.
If you are later resumed with review findings: fix them, re-run the covering tests, append a fix report (changes, command, output) to the same file, reply with the same short format.
```

## Task reviewer (spec + quality)

```
Review ONE task's implementation. Read-only: do not modify files, the index, HEAD or branches. Do not spawn subagents.

Requested: <brief file>. Binding constraints: <verbatim global constraints>.
Implementer's claims (unverified, don't trust them): <report file>.
Diff: <diff file> (base <sha>, head <sha>). Read it once. Look outside the diff only to check a specific risk you name.
The implementer already ran the tests. Re-run only a focused test when a specific doubt requires it.

Part 1 — Spec compliance: Missing (skipped or claimed but not built) · Extra (unrequested features or over-engineering) · Misunderstood. List requirements you cannot verify from the diff as ⚠️.
Part 2 — Quality: correctness and edge cases, error handling (nothing swallowed), tests assert real behavior (not mocks), no duplication of existing helpers, focused files, quality floor intact, secure handling of input and secrets.

Severity: Critical (security/data loss/broken) · Important (wrong or fragile behavior, missed requirement, tests that assert nothing, duplicated logic) · Minor (polish). A plan-mandated defect is still a finding: label it "plan-mandated". Every finding needs file:line, why it matters, and the fix.

Output, starting immediately:
### Spec: ✅ compliant | ❌ <issues> · ⚠️ <cannot verify>
### Strengths (specific)
### Issues — Critical / Important / Minor
### Verdict: Approved | Needs fixes — <1–2 sentence reason>
```

## Scoped re-review (after a fix round)

```
Read-only re-review of a FIX, not a full review. Findings being fixed (verbatim): <list>.
Brief: <brief file>. Report with fix notes: <report file>. Fix diff: <diff file> (<fix base>..<head>).
For each finding: ADDRESSED (file:line evidence) | NOT ADDRESSED (why).
Flag only NEW Critical/Important breakage introduced by this fix diff. Put other observations under "Out of scope (deferred)".
```

## Final reviewer (whole branch or large/risky diff), model `opus`

```
Senior engineer, fresh eyes, read-only. Do not spawn subagents.
What it should do: <spec path> (+ plan path). Diff of the whole change: <diff file> (merge-base <sha>..<head>).
Deferred minors and parked findings to triage (fix-before-merge or truly later): <ledger lines>.

Review: requirements fully met (and nothing extra) · correctness incl. null/empty/error paths · data safety (atomic updates, unique constraints, transactions, parameterized queries) · security (input validation, authz on every action, XSS, secrets, untrusted third-party and LLM output) · concurrency and idempotency · new enum/status values handled by every consumer · performance (N+1, unbounded work) · architecture fit (reuse of existing helpers, boundaries, file size) · tests would catch regressions · migrations reversible and backward-compatible · observability for new critical paths.
Cite evidence (file:line) for both problems and "this is safe" claims. Don't list preferences as issues.

Output: Ready to merge: YES | NO | WITH FIXES · Critical · Important · Minor · Triage of deferred items · 1-paragraph assessment.
```

## Doubt reviewer (adversarial, high-stakes decisions)

```
Adversarial review. Find what is WRONG with this artifact. Assume the author is overconfident.
Look for: unstated assumptions · unhandled edge cases · hidden coupling or shared state · ways the contract can be violated (concurrency, retries, partial failure, bad input, ordering) · broken conventions · irreversible consequences.
Do NOT validate or summarize. Report issues, each with a concrete failing scenario, or state explicitly that none were found after thorough examination.
Read-only; do not spawn subagents.

ARTIFACT: <code/diff/decision in 3–5 sentences, or a file path>
CONTRACT: <what it must guarantee: requirements, invariants, constraints>
```
(Never include your own conclusion or reasoning; that biases the reviewer toward agreeing.)

## Parallel investigator (independent failures)

```
Investigate and fix ONLY: <one test file or subsystem>. Failures: <test names + exact error messages>.
Constraints: don't change code outside <scope>; don't weaken or skip tests; find the root cause (no longer timeouts, no retries masking bugs); use condition-based waiting instead of sleeps.
Follow: reproduce → trace to root cause → failing test (existing) → minimal fix → run this file + related suite.
Return: root cause (1–3 lines), files changed, test output summary, anything that may affect other areas.
```

## Research helper (`subagent_type: Explore`)

```
Find <what> across the codebase. Breadth: <medium | very thorough>. Return only the conclusion: locations (file:line), the pattern used, and anything surprising, in under 30 lines.
```
