# DEFINE: decide what to build before any code exists

**Output:** a confirmed statement of intent, a chosen approach, and a saved spec.
**Hard gate:** no code, scaffolding or project setup until the owner approves. The cheapest moment to catch "that's not what I meant" is now.

Skip steps that are already answered, but never skip the premise check (§4), the alternatives (§6) or the restate (§7) on the Product tier.

## 0. Start from what's known

- If the prompt-optimizer produced a task brief this turn, treat the assumptions it resolved as answered. Don't re-ask them.
- In an existing repo, read `CLAUDE.md`, `README`, `TODOS.md`, `docs/specs/`, `docs/decisions/` and `git log --oneline -20`.
- **Scope check first.** If the request bundles several independent capabilities (for example "a marketplace with payments, chat and an admin panel"), don't refine details yet. Propose a **capability map** and a build order, get it approved, then define only the first module:

```
| Module id | Responsibility | Depends on |
| accounts  | sign-up, login  | —          |
| listings  | create/browse   | accounts   |
Build order: accounts → listings → payments
```

## 1. Pick the mode (ask once if it isn't obvious)

- **Product mode:** a startup, a career product, or anything with customers, revenue or a public launch.
- **Builder mode:** a personal tool, learning project, demo, hackathon or just for fun.

If money or customers enter the conversation, move up to Product mode.

## 2. Interview until you can predict the answers

Open with your current read and an honest number:

```
HYPOTHESIS: You want <one sentence>.
CONFIDENCE: ~40%. Still missing: who it's for, what "done" looks like.
```

- Ask **one question at a time**, each with your **GUESS** attached: people react to a wrong guess faster than they invent an answer.
- **Stop** when you can predict the owner's reaction to your next three questions. If several rounds pass and confidence isn't rising, say so and step back.
- Probe answers that sound like what one *should* want ("scalable", "modern", "like Airbnb", "best practice") with: *"If you didn't have to justify this to anyone, what would you actually want?"*
- "Whatever you think" is not a decision about direction. Offer two concrete options instead.

**Product mode: forcing questions.** Route by stage and skip what's answered: pre-product Q1–Q3; has users Q2, Q4, Q5; paying customers Q4–Q6. Push once more on any vague answer.
1. **Demand reality:** what's the strongest evidence that someone would be upset if this disappeared tomorrow? A waitlist or "that's interesting" doesn't count; behavior and money do.
2. **Status quo:** what do they do today to solve it, even badly, and what does that cost them?
3. **Desperate specificity:** name the actual person who needs this most. What is their role, and what happens to them if it stays unsolved?
4. **Narrowest wedge:** what's the smallest version someone would pay for this week?
5. **Observation:** have you watched someone use it (or the workaround) without helping? What surprised you?
6. **Future-fit:** in 3 years, does this become more essential or less, and why?

Posture: direct and warm. Take a position on each answer and say what evidence would change it. Name failure patterns you recognize ("solution looking for a problem", "interest isn't demand"). If the owner wants to skip, ask the 2 most critical remaining questions and move on; on a second push, move on.

**Builder mode questions** (generative): What's the coolest version? Who would you show it to? What's the fastest path to something you can use? What existing thing is closest, and how is yours different?

## 3. Look at the landscape (search before building)

Use `firecrawl-web-reading`. Search with **generic category terms**, never the owner's private idea or name; ask first if the idea looks confidential.
- **Layer 1:** what everyone already knows works. **Layer 2:** what current discussion says (scrutinize it). **Layer 3:** first principles for this specific case.
- If conventional wisdom is wrong here, name it: `EUREKA: everyone does X assuming Y; our evidence says Y is false because…`. Otherwise say the conventional approach is sound.
- **Say it plainly if something already solves this:** an existing product, open-source tool, no-code tool or template. Building may be the wrong move, and saying so is part of the job.

## 4. Challenge the premises

```
PREMISES:
1. This is the right problem: <statement>. Agree?
2. Doing nothing costs: <statement>. Agree?
3. Existing code/tools already cover: <statement>. Agree?
4. Users will get it via: <hosting / app store / link / package>. Agree?
```

If the owner disagrees with a premise, revise and loop back.

## 5. Generate variations (only when the idea is still fuzzy)

Invoke `product-management:product-brainstorming` for divergent variations: inversion, 10x simpler, a different audience, combination, the 10x version. Converge to 2–3 directions and stress-test each on user value, feasibility, differentiation and what would kill it.

## 6. Alternatives (mandatory on the Product tier)

```
APPROACH A: Minimal viable (fewest moving parts, ships fastest)
  Summary / Effort (human team vs AI-assisted) / Risk / Pros / Cons / Reuses
APPROACH B: Ideal architecture (best long-term path)
APPROACH C: Lateral (optional: a different framing of the problem)
RECOMMENDATION: <X> because <reason tied to the owner's goal>
```

Present with AskUserQuestion. **STOP** until the owner chooses. A "clearly winning" approach still needs a yes.

**Scope mode** (once the direction is chosen): Expand, Selective (default for new products and enhancements), Hold (default for bug fixes and refactors) or Reduce (suggest it when more than 15 files are touched). In Expand or Selective mode, offer **at most 4 expansion candidates in one multiSelect question**. Describe each by what the user will feel, plus effort and risk. Accepted candidates join the scope; the rest go on the "Not doing" list.

## 7. Restate and confirm

```
Here's what I'll build:
- Outcome:      <one line>
- For:          <who>
- Why now:      <one line>
- Success:      <measurable: "a visitor can book in under 60 seconds">
- Constraint:   <budget / deadline / platform>
- Not doing:    <explicit exclusions>
Yes / change something?
```

You need an explicit yes. "Sounds good" gets the follow-up "anything you'd refine?". Turn vague goals into measurable criteria ("fast" becomes "page usable in under 2.5s on mobile").

## 8. Write the spec

1. For user-facing features, invoke `product-management:write-spec` for the product half: problem, users, goals and non-goals, success metrics, user stories with acceptance criteria.
2. Add the technical half. You decide it and explain each choice in one plain line:

```markdown
# Spec: <name>
## Objective and success criteria (testable)
## Scope / Not doing (and why)
## Chosen approach (and rejected alternatives, one line each)
## Tech stack (exact versions, verified in official docs)
## Commands (dev / build / test / lint: exact)
## Project structure
## Data and interfaces (entities, fields, API shapes)
## Quality bar (performance, accessibility, security needs beyond the Definition of Done)
## Boundaries: Always / Ask first / Never
## Distribution and running costs (where it lives, who pays what)
## Risks and open questions
```

**Stack choice for a non-technical owner:** boring, well-documented, popular (so help exists), managed hosting with a free or cheap tier, few moving parts, and at most one "innovation token" (one new or unusual technology) per project. Check current versions and pricing in the official docs; never rely on memory.

3. **Self-review the spec:** remove placeholders and TBDs, fix contradictions, pick one reading for anything ambiguous, and confirm it fits one plan (otherwise decompose).
4. Save it to `docs/specs/YYYY-MM-DD-<topic>.md`, confirm the plain-language summary with the owner (they don't need to read the file), then go to PLAN.
