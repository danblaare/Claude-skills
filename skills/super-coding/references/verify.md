# VERIFY: prove it, then show it

## 1. The gate function (before any claim of done, fixed, passing or working)

```
1. IDENTIFY the command/check that proves the claim
2. RUN it fresh and complete (not an earlier run, not a subset)
3. READ the whole output: exit code, failure count, warnings
4. CLAIM only what the output shows; otherwise state the real status with the evidence
```

| Claim | Requires | Not enough |
|---|---|---|
| Tests pass | Test run output, 0 failures, this turn | An earlier run, "should pass" |
| Build works | Build command exit 0 | Lint passing |
| Bug fixed | Original scenario now passes, regression test red→green proven | Code changed |
| Feature done | Every acceptance criterion checked, app run for real | Tests passing |
| Helper agent finished | Your own `git diff` + test run | Its report |
| Deployed | Production URL checked (ship.md §5) | Deploy command succeeded |

## 2. Definition of Done (the standing bar, on top of each task's acceptance criteria)

**Correctness:** acceptance criteria met · verified **at runtime**, not just compiled · new behavior has tests that fail without it · no regressions · edge cases and error paths handled.
**Quality:** clear naming · no duplicated logic · no dead code, debug output or commented-out blocks · scoped to the task · lint and format clean · quality floor intact (build.md §9).
**Integration:** works with the rest of the system · migrations, config and flags accounted for · public interfaces backward compatible.
**Documentation:** user-facing behavior and setup documented · hard-to-reverse decisions recorded · `CLAUDE.md` commands still accurate.
**Ship-readiness** (anything real users touch): security reviewed where input, auth or data is involved · critical paths observable · a rollback path exists · **the owner has seen it working**.

## 3. Run it for real

Invoke **`run`** to launch the app and see the change working, not just the tests.

**Web apps: browser QA with the Playwright MCP** (preferred browser; load the tools with ToolSearch when needed):

| Mode | When | Covers |
|---|---|---|
| **Diff-aware** (default on a branch) | After building a feature | Map changed files → affected pages/routes/APIs; test those and their neighbors |
| **Quick** | Smoke check after small changes | Home + top 5 navigation targets: loads? console errors? broken links? |
| **Full** | Before a launch | Every reachable page, 5–10 well-evidenced issues |
| **Regression** | After fixes / before a release | Re-run and compare with the previous report in `docs/qa/` |

**Per page:** take a screenshot, read console errors and failed network requests, click every interactive element, and test forms with empty, invalid, edge-case (very long text, special characters) and valid submissions, watching for double-submit. Check navigation in and out, the back button, and the **empty, loading, error and overflow** states. Check the **mobile viewport (375px)** as well as desktop, and Tab through with the keyboard.

**Sign-in walls:** the owner signs in themselves in the browser window. **Never type their passwords, one-time codes or payment details.** CAPTCHAs are for the owner to solve. Use test accounts and sandbox or test-mode payments wherever possible.

**Evidence per issue:** reproduction steps, before and after screenshots, console output.
**Severity:** critical (core flow blocked, data loss, security) · high (a feature broken) · medium (visible defect with a workaround) · low (cosmetic).
**Health score:** start at 10; critical −3, high −2, medium −1, low −0.5; floor 0. Report `baseline → final`.

**Fix loop.** Tier Quick fixes critical and high; Standard (the default) adds medium; Exhaustive fixes everything. For each issue in severity order:
1. Locate the source and make the **minimal** fix. For UI, prefer CSS or styling changes over structural ones.
2. Add a regression test when the bug involves behavior (logic, forms, data flow). Pure CSS doesn't need one.
3. Re-test in the browser with an after-screenshot.
4. Make one commit per fix, if authorized.
5. Classify it as verified, best-effort (couldn't fully confirm) or reverted (it made things worse, so revert immediately).

**Self-regulate every 5 fixes.** Risk starts at 0: +15% per revert, +5% per fix touching more than 3 files, +20% for touching unrelated files, +10% if only low-severity issues remain. **Over 20%: stop** and report to the owner. Hard cap: 30 fixes per session. If the final score is **worse** than the baseline, say so prominently.

Save the report to `docs/qa/qa-report-YYYY-MM-DD.md` with screenshots in `docs/qa/screenshots/`: issues, fix status, commits, score delta, and a one-line summary ("QA found N issues, fixed M, health X → Y").

**UI quality checks:** invoke `design:accessibility-review` (WCAG 2.1 AA) and `design:design-critique` on the key screenshots, and apply the frontend.md slop checklist. Fix findings through the same loop.

**Non-web software:**
- **CLI / scripts:** run real commands with real, missing and malformed inputs; check exit codes and error messages.
- **APIs:** call each endpoint (curl or a test client) with valid, invalid, unauthenticated and forbidden requests; confirm status codes and the error shape.
- **Automations / bots:** a dry run or sandbox run end to end, including the failure path (API down, bad data).

## 4. Show the owner

Never just say "it's done". Show it: screenshots or a short sequence, a local URL they can open, and a 3-step "try this" guide for the core flow. Ask them to try it. Their reaction is acceptance testing. Anything they find goes back through DEBUG or BUILD.
