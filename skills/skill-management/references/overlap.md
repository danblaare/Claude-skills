# Overlaps, conflicts and trigger tests

## Overlap and conflict review
1. **Gather:**
   - `inventory --full` for user skill descriptions.
   - The plugin and account skills from this session's available-skills list (name plus description).
   - The user's standing preferences from memory or CLAUDE.md (for example preferred tools for reading the web, scraping or browser automation).
2. **Compare descriptions** and group skills that would start on the same kind of request. Examples: security review (security-and-hardening vs /security-review vs engineering:code-review); web reading (firecrawl-web-reading vs copilot-web-fetch); debugging (engineering:debug vs others).
3. **Classify each group:**
   - **Duplicate:** does the same job; keep one.
   - **Complementary:** different moments, e.g. one guides while writing and one reviews afterwards; keep both, and optionally sharpen descriptions so they don't compete.
   - **Conflict:** contradicting instructions, e.g. a skill telling Claude to use a different browser tool, or to skip tests; resolve.
4. **Read the SKILL.md bodies** of user skills in each group to confirm conflicts. Plugin skills can only be judged by description.
5. **Report plain-English groups:**
   - Which skills compete.
   - What the user may notice (inconsistent answers, the wrong skill starting, extra cost).
   - A recommendation: keep both / disable X / reword X's description so it starts only when … .
6. **Offer fixes:** changes go through `references/remove.md` or `references/create-edit.md`. Plugin skills can only be toggled in the Claude app.

## Trigger tester
Checks whether a skill starts when it should and not when it shouldn't, by running real prompts through the `claude` CLI in an isolated folder with editing, shell and web tools blocked. These sessions don't count in usage stats.

1. **Draft prompts:** 2–4 that should start the skill, and 1–3 near-misses that shouldn't. Show them and confirm.
2. **State the cost before running:** about $0.05–$0.20 per prompt of the user's Claude usage.
3. **Run:**
   - `trigger-test --prompt "…" --prompt "…" --expect <skill>` for the should-start prompts.
   - The same with `--expect-not` for the near-misses.
   - Default `--max-turns 1`; use 2 if nothing triggers but a skill should have.
4. **Report** a pass/fail table and which skill started instead.
5. **For failures,** propose description wording that fixes them, apply it on approval (`references/create-edit.md`), and offer a re-test.

Without the CLI, or if the user declines the cost: predict triggering by reading all descriptions, and say it's a prediction.
