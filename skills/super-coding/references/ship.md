# SHIP: integrate, release, deploy, watch

Every push, pull request, deploy or publish needs the owner's explicit yes **for that action**. Never force-push, never skip hooks (`--no-verify`), never disable failing CI checks.

## 1. Pre-ship gate

1. **Fresh evidence** on the exact tree being shipped: full test suite, build, typecheck, lint. If anything changed since the last run (including review fixes), re-run it.
2. REVIEW and VERIFY are complete, and the owner has seen the feature working.
3. Invoke **`engineering:deploy-checklist`** and fill every line with real evidence, not ticks. Also confirm:
   - A rollback plan is written (§5).
   - Environment variables and secrets exist in the hosting dashboard, entered by the owner.
   - Database migrations are backward-compatible (backend-data.md, expand/contract).
   - Risky features are behind a flag that is off by default.
   - Error reporting and logging are on (§6), and docs are updated (§7).
4. **Public launch extras:**
   - Security headers, rate limiting on auth, CORS restricted to known origins (not `*`).
   - The dependency audit (`npm audit` / `pip-audit`) shows no high or critical issues.
   - Core Web Vitals are good and accessibility meets AA.
   - No debug output or test accounts in production.
   - If the product collects personal data, takes payments, or targets the EU or minors, invoke **`legal:compliance-check`** and flag the needs (privacy policy, terms, cookie consent). Tell the owner to get real legal review; don't present it as legal advice.

## 2. Integrate the branch

Present **exactly these options** with AskUserQuestion:
1. **Merge into main locally.** Recommended when there's no GitHub remote or CI.
2. **Push and open a Pull Request.** Recommended when the repo is on GitHub with CI or deploy previews.
3. **Keep the branch for later.**

- **Merge:** switch to the base branch, pull, merge, and **run the tests on the merged result**. If they fail, stop and keep the branch. Delete the branch only after a green merge.
- **Pull Request:** needs a remote and the `gh` CLI. If `gh` is missing, offer to install it (through `skilltotal-preinstall`); the owner runs `gh auth login` themselves. Otherwise push and give the owner the compare link. PR body: what and why, how it was tested (evidence), screenshots, risks, rollback. Replies to review comments go in the comment threads.
- **Discard** only if the owner explicitly asks and types `discard` after seeing exactly what will be deleted.
- A rejected push means the remote moved. Investigate; never force.

## 3. Commits, versions, changelog

- **Atomic commits:** one logical change each, `type: why` (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`). Refactors are separate from features. Order: infrastructure → models/services with their tests → UI with its tests → version/changelog.
- **Before every commit:** review `git diff --staged` and scan it for secrets (keys, tokens, `.env` content). Commit only generated files the project expects (lockfiles, migrations).
- **Versions (semver)** for anything others depend on or that users update: breaking change → MAJOR, new feature → MINOR, fix → PATCH. When unsure whether a change breaks things, treat it as breaking. Tag releases (`git tag -a vX.Y.Z`), and let the tag be the source of truth.
- **`CHANGELOG.md`** is written for users, not as a copy of the git log. Group entries under Added / Changed / Fixed / Deprecated / Removed / Security, newest first, each phrased by user impact ("You can now…"). Write the entry with the change, not at release time. Never delete or regenerate past entries.

## 4. Deploy

**First deploy of a project: teacher mode.** Walk the owner through it and explain what each piece is for.
1. **Detect or recommend a platform that fits the stack.** Check current features and free tiers with `firecrawl-web-reading` before recommending, and state monthly cost. Typical fits:
   - static sites → Cloudflare Pages / Netlify / GitHub Pages
   - Next.js → Vercel
   - apps with a server → Render / Railway / Fly.io
   - database and auth → managed Postgres (Supabase, Neon)
   - mobile → Expo EAS
2. **The owner creates the accounts**, adds payment methods, connects the repo in the platform UI, and pastes secrets into the platform's environment settings. Never ask for them in chat, and never enter them yourself.
3. Any platform CLI gets installed through `skilltotal-preinstall` first.
4. Record the configuration in `CLAUDE.md` under `## Deploy`: platform, production URL, preview URL pattern, health-check URL, deploy command or trigger, rollback command, where logs and errors are.
5. **CI** (once a GitHub remote exists): a minimal GitHub Actions workflow running install → lint → typecheck → test → build (→ dependency audit) on pull requests and pushes to main. Secrets go in repository secrets only. Block merges on red checks. Fix slow CI with caching and parallel jobs, not by skipping steps.

**Every deploy:**
- **Preview or staging first** when the platform supports it. Smoke-test the preview with Playwright (verify.md, Quick mode).
- **Production deploy only after the owner says yes.**
- Don't deploy late on a Friday, or right before being unreachable, without saying that's a risk.

## 5. Right after deploying (canary check) and rollback

**Within minutes:**
1. The health-check URL returns 200.
2. Open the **production** URL with Playwright: key pages load, no console errors, the **core flow works end to end**, screenshots match the preview.
3. The error-reporting dashboard and logs show no new error types.
4. If a migration ran: data reads and writes still work.

**Red signals:** new error types, an error rate above twice normal, the core flow broken, latency up more than 50%, data-integrity problems. Recommend a rollback in plain words ("switch back to yesterday's version; nothing is lost; takes ~2 minutes") and do it on the owner's yes. Offer extended watching (for example, a check every 10 minutes for an hour with the `loop` skill) only if the owner wants it.

**Rollback plan** (write it before deploying):

```markdown
## Rollback: <release>
Triggers: <error types / thresholds / broken flow>
Steps: 1) turn off flag <name> OR redeploy previous version via <platform action/command>
       2) verify health check + core flow  3) tell the owner what happened
Data: migration <X> down path: <command>; data created by the new feature: <kept/cleaned>
Time to recover: flag < 1 min · redeploy < 5 min · database < 15 min
```

## 6. Observability (anything with real users)

- **First, write 2–4 questions** you'll need answered when it breaks ("did the payment succeed? why did signup fail?"). Every signal must serve one of them.
- **Error tracking** for frontend and backend (for example Sentry; its package goes through `skilltotal-preinstall`) plus an **uptime check** on the health URL.
- **Structured logs:** a stable event name plus fields plus a request or correlation ID, in JSON. **Never log secrets, tokens, passwords or full personal data.**
- **APIs under real load:** rate, errors and duration (p95/p99, not averages), with labels drawn only from small fixed sets.
- **Alerts on symptoms users feel** (error rate, core flow failing, very slow responses), never on noise. Each alert gets a 3-line runbook in `docs/runbooks/`: what it means, what to check first, who to call.
- Verify the telemetry itself: force one error on staging and find it in the dashboard.

## 7. Docs sync after shipping

- The `README` quick start still works as written (run it). `CLAUDE.md` commands, conventions and deploy section are current.
- Flag architecture diagrams that no longer match the code.
- `TODOS.md`: mark items complete **only with clear evidence in the diff**, and add anything deferred.
- New READMEs, API docs or runbooks: invoke `engineering:documentation`.
- Hard-to-reverse decisions made during the build: ADR in `docs/decisions/`.

## 8. Retro (optional, after a launch or weekly)

From `git log` over the period: what shipped, the most-changed files (hotspots), areas with repeated fixes (architecture smells), how many changes came with tests, and deferred items. Write `docs/retros/YYYY-MM-DD.md` in plain language: 3 wins, 3 things to improve, 1 focus for next time.
