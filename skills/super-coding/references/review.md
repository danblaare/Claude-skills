# REVIEW: find what tests don't catch, before anything is called done

Order: scope check → automated review → five-axis and critical pass → quality-floor guard → fix-first → simplify → re-test.
The owner can't review code, so this phase is their protection. Be rigorous, and never rubber-stamp.

## 1. Scope drift

Compare the diff (`git diff <base>...HEAD`, plus untracked files) with the spec or plan task:
- **Missing:** a requirement that isn't implemented, or was claimed without being implemented.
- **Extra:** anything unrequested (features, options, abstractions).

Both are findings.

## 2. Automated diff review

Invoke the built-in **`code-review`** skill on the current diff. Use effort `medium` for Bounded work and `high` for Product work, auth, payments or data changes. Never use `ultra`: it is user-triggered and billed. For auth, payments, uploads or personal-data changes, also invoke **`security-review`** and follow **`security-and-hardening`**. Changes to hot paths go through **`performance-optimization`**.

## 3. Five axes plus the critical pass (what the tools may miss)

**Correctness:** matches the spec; handles null, empty and boundary values; covers error paths as well as the happy path; no off-by-one errors or inconsistent state.
**Readability and simplicity:** could it be fewer lines? Does every abstraction earn its keep (don't generalize before the third use)? Are conditionals bolted onto unrelated flows? Do names say what things do?
**Architecture:** follows existing patterns; no near-duplicate of an existing helper; no feature logic in shared modules; dependencies flow one way; no file pushed past ~1000 lines without splitting it.
**Security:** input validated at boundaries, output encoded, parameterized queries, auth checked on every protected action, no secrets, external data treated as untrusted.
**Performance:** no N+1 queries, unbounded loops or fetches, or missing pagination; no needless re-renders; no blocking calls in async code.

**Critical pass** (read code **outside** the diff when needed):
- **Data safety:** string-built SQL; check-then-act races (should be an atomic `UPDATE … WHERE`); find-or-create without a unique index; status transitions not guarded by the old status; model validations bypassed.
- **Unsafe HTML:** `dangerouslySetInnerHTML` / `v-html` / `|safe` on user data (XSS).
- **LLM output trust boundary:** model output written to the database, emailed, fetched as a URL (SSRF) or executed without schema or format validation; model output stored and later fed back into prompts (stored prompt injection).
- **Shell and eval:** command strings built with interpolation (use argument arrays); `eval` on dynamic input.
- **Enum/value completeness:** for a new status, role or type value, grep **every** consumer of its sibling values and read each one. Does it handle the new value, or fall through to a wrong default?
- **Time:** timezone or day-boundary assumptions; mismatched time windows between related features.
- **Type coercion across boundaries** (JSON ↔ JS ↔ DB): numbers vs strings, especially in hashes and IDs.
- **Completeness gaps:** a feature at 80–90% when finishing it is a small, contained effort (missing error path, missing negative test, partial enum handling).

## 4. Quality-floor guard (mechanical, on the diff)

New suppressions (`@ts-ignore`, `eslint-disable`, `noqa`, `type: ignore`, coverage-ignore) · `.skip` / deleted tests / removed assertions · empty catch, "not implemented" stubs, TODOs in place of code · lowered thresholds or disabled CI steps · secrets · unexplained new exceptions. Each one is **Important** until justified.

## 5. Tests and dependencies

- Every new behavior has a test that would **fail if the behavior broke**. Names describe behavior. No test only checks that "it renders" or "it doesn't throw".
- Dependency changes: changelog read (a "patch" can change behavior), one dependency per change, lockfile diff reviewed, `skilltotal-preinstall` done.
- **Dead code:** remove orphans **this change** created. List pre-existing unused code and ask before deleting it.

## 6. Severity and fix-first

| Severity | Meaning | Action |
|---|---|---|
| **Critical** | Security hole, data loss, broken core flow | Fix now; blocks done |
| **Important** | Wrong or fragile behavior, missed requirement, maintainability damage | Fix before done |
| **Minor** | Worth doing, not blocking | TODOS.md or ledger |
| **Nit** | Preference | Skip unless trivial |

**AUTO-FIX** (mechanical; a senior engineer wouldn't debate it): dead code, unused variables, N+1 fixed with eager loading, magic numbers turned into named constants, stale comments, missing validation of model output, path or version mismatches. Output one line per fix: `[AUTO-FIXED] file:line problem → fix`.

**DECIDE-AND-LOG** (technical judgment the owner can't meaningfully weigh in on, such as a race-condition fix or an internal design choice): choose the safest well-understood option, fix it, and log a Ruling.

**ASK THE OWNER** only when the fix changes **what users see or can do**, removes functionality, costs money, or trades risk against speed. Frame it as: "Found: <problem in user terms>. Impact: <who and what>. Recommend: <fix> (<effort>)."

**Back every claim with evidence.** "This is safe" cites the line that makes it safe; "handled elsewhere" cites the handling code; "tests cover this" names the test. "Looks fine" is not a finding. Don't flag harmless redundancy, preference-only consistency changes, or anything the diff already addresses.

## 7. Simplify, then re-verify

Invoke the built-in **`simplify`** skill on the changed code, then re-run tests, typecheck and lint.

**Refactoring rules** (whenever you restructure code):
- **Preserve behavior exactly:** existing tests pass **without modification**. If a test needs changing, you changed behavior.
- **Chesterton's fence:** understand why the code exists (read the callers, check `git log -L` / blame) before removing it.
- Stay scoped to recently changed code unless the owner asked for more.
- One simplification at a time, with tests after each. Keep refactor commits separate from feature commits.
- Choose clarity over cleverness and line count: no nested ternaries or dense reduce-chains, and don't over-inline named concepts.
- A refactor that only **moves** complexity isn't a simplification. Prefer changes that make whole branches or layers disappear.
- For a repo-wide "what should we clean up?", invoke `engineering:tech-debt` to prioritize, then take items one by one through this pipeline.

## 8. Independent reviewer for big or risky diffs

For diffs over ~300 lines, or ones touching auth, payments, data migrations or public APIs, dispatch the **Final reviewer** (`references/prompts.md`, model `opus`) with the spec path and a diff file. It gets fresh context and never sees your reasoning. Then handle its findings with §9.

## 9. Receiving feedback (from reviewers, tools, other AIs, or the owner)

1. **Read everything** before acting, then **restate** each item technically.
2. **Verify it against the codebase:** is it true here? Would it break something? Is there a reason for the current code?
3. **Clarify unclear items before implementing any items**, because they may be related.
4. **Respond with a fix or reasoned pushback.** No performative agreement ("Great point!"), no thanks, just the fix or the technical reason.
5. **Implement one item at a time,** blocking issues first, testing each.
6. **YAGNI check:** before "implementing properly", grep for actual usage. If nothing uses it, propose removing it instead.
7. **The owner's product decisions outrank any reviewer.** Suggestions that change the owner's stated direction get presented, never silently applied, even when several models agree.
