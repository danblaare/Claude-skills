# DEBUG: root cause first, always

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

**Start:** invoke `engineering:debug` for the session frame (reproduce → isolate → diagnose → fix) and its report. The rules below are stricter and win on any conflict. Use the process **especially** when a fix looks obvious, when under time pressure, or after a fix already failed.

**Users affected right now?** Invoke `engineering:incident-response` first: stabilize (roll back, turn off the feature flag, or show a maintenance page, **with the owner's yes**), then investigate calmly.

## Phase 1: Investigate (no fixes yet)

1. **Read the whole error.** Read the full message and stack trace, and note the file, line and error code; they often contain the answer.
2. **Reproduce reliably.** Get the exact steps. If you can't reproduce it, gather more data (logs, screenshots, the owner's exact clicks, one question at a time). Don't guess. For UI bugs, reproduce with the Playwright MCP and capture console errors and failed network requests.
3. **Check what changed:** `git log --oneline -20 -- <area>`, `git diff`, new dependencies, config and environment variables. A regression means the cause is in a diff.
4. **Systems with several parts** (browser → API → database, or CI → build → deploy): add temporary logging at **each boundary** (what enters, what leaves, which config is present) and run once to find **which layer** breaks. Then dig into that layer only.
5. **Trace backward:** where does the bad value come from, and who passed it in? Keep going up until you reach the source. Fix at the source, not where it crashed.

**Output:** `Root cause hypothesis: <X> because <Y>`, a specific, testable claim.
**Scope lock:** name the narrowest folder that contains the cause, and don't edit outside it without saying why.

## Phase 2: Find the pattern

- Find **similar code that works** in this repo, then list **every** difference, however small.
- If you're applying a pattern from docs, read the reference **completely**, not skimmed.
- Known shapes:

| Pattern | Signature | Look at |
|---|---|---|
| Race condition | Intermittent, timing-dependent | Shared state, concurrent requests, async ordering |
| Null propagation | "undefined is not…", TypeError | Missing guards on optional values, API shape changes |
| State corruption | Inconsistent or partial data | Transactions, multi-step writes, callbacks |
| Integration failure | Timeouts, unexpected responses | External APIs, auth tokens, rate limits |
| Config drift | Works locally, fails deployed | Env vars, build settings, feature flags, database state |
| Stale cache | Old data until refresh | CDN, browser cache, framework caching, service workers |

- **The same files keep breaking?** That's an architecture smell, not bad luck. Say so.
- Unfamiliar error: search the **sanitized, generic** error type plus the framework version via `firecrawl-web-reading`. Strip URLs, keys, file paths and customer data first.

## Phase 3: Test the hypothesis

- Probe with the **smallest** change (a log line or an assertion), one variable at a time.
- If it's confirmed, go to Phase 4. If it's wrong, form a **new** hypothesis from the new evidence. Never stack fixes.
- Say "I don't understand X yet" instead of pretending.
- **3 failed hypotheses → STOP.** Tell the owner in plain language and ask: (A) continue with a named new hypothesis, (B) add logging and catch it next time, (C) bring in expert help.

## Phase 4: Fix

1. **Write the failing regression test first.** It reproduces the bug, and you've watched it fail.
2. **Make one fix at the root cause.** Minimal diff, no bundled refactors.
3. **Prove red → green:** the test passes with the fix, **fails with the fix reverted**, and passes again once restored. Then run the full suite.
4. **Blast radius:** if the fix touches more than 5 files, ask the owner (proceed / split / rethink) before continuing.
5. **Fix didn't work?** Count your attempts. Under 3, return to Phase 1 with the new information. **At 3, stop**: each fix revealing a new problem means the structure is wrong. Discuss an architectural change with the owner instead of trying a 4th fix.
6. **Defense in depth** after the root fix, where corrupt data would be costly: validate at the entry point, in the business logic, and with an environment guard (for example, refusing to run destructive test code against production).
7. **Remove temporary logging.** Keep only intentional, structured logs.

## Phase 5: Verify and report

Re-run the **original** scenario (in the browser for UI bugs) and the full suite, and paste the evidence.

```
DEBUG REPORT
Symptom:         <what the owner saw>
Root cause:      <what was actually wrong, in plain language>
Fix:             <what changed, file:line>
Evidence:        <test output / reproduction now passing / screenshot>
Regression test: <file:line>
Related risks:   <similar code that may share the bug, TODOs added>
Status:          DONE | DONE_WITH_CONCERNS | BLOCKED
```

**"No root cause found"** (a truly external, timing or environment issue): document what you investigated, add handling (retry with backoff, timeout, a clear user message) plus structured logging to catch it next time. Be suspicious of this outcome, because most "no root cause" cases are unfinished investigations.

## Red flags: return to Phase 1

"Quick fix for now" · "just try changing X" · several changes before re-running · proposing fixes before tracing the data flow · "it's probably X" · "I don't fully understand but this might work" · a fix that reveals a new problem somewhere else · the owner asking "is that actually happening?" or "stop guessing".
