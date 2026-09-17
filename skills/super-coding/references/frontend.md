# FRONTEND / UI: intentional, accessible, not AI-generic

## 1. Design source of truth first

- **No design system yet?** Before building screens, ask the owner 2–3 taste questions (the feeling in three words; 1–3 sites they like and why; light, dark or both; existing logo or colors). Then invoke **`design:design-system`** to define the tokens: color (brand, semantic, neutrals), type scale, spacing scale, radius, shadows, motion. Save them as `DESIGN.md` plus a theme or tokens file. Show a small preview page before building features.
- **Existing product:** infer the system from the code, use its tokens, and invent no new values.
- Use semantic tokens (`text-primary`, `bg-surface`), never raw hex or pixel values scattered through components.

## 2. Design principles (use them to explain every choice)

1. **Hierarchy:** every screen answers what the user sees first, second and third. If everything competes, nothing wins.
2. **Empty states are features:** say what this is, why it's empty, and give the primary action to start.
3. **Specific over vibes:** "clean and modern" isn't a decision; name the font, spacing and interaction pattern.
4. **Edge cases are real experiences:** 47-character names, zero results, errors, slow networks, first-time vs returning users.
5. **Subtraction by default:** if an element doesn't earn its pixels, cut it.
6. **Responsive is intentional** at 320 / 768 / 1024 / 1440px. Mobile isn't just a stacked desktop.
7. **Trust is built at pixel level,** especially around money, personal data and destructive actions.

## 3. AI-slop blacklist: don't ship these defaults

Purple or indigo gradients as the "brand" · gradients everywhere · max rounding on every element · generic hero + 3-column feature grid + testimonial template · lorem ipsum or "Welcome to <App>" copy · the same large padding everywhere · uniform stock card grids that ignore priority · heavy layered shadows · emoji as icons · everything centered · decorative blobs with no meaning.
Use the project's real palette, **real content** (it exposes layout problems) and purpose-driven layouts.

## 4. Components and state

- Composition over configuration (`<Card><CardHeader/>…` rather than 12 props). Keep components focused, and split any over ~200 lines.
- Separate data fetching (a container) from presentation. Handle loading, error and empty in the container.
- Pick the **simplest state that works:** local → lifted (2–3 siblings) → URL params (filters, pagination, shareable state) → a server-state library (remote data and caching) → a global store (only for complex app-wide client state). No prop drilling deeper than 3 levels.
- Colocate a component, its test and its hook.

## 5. Every screen has all its states

**Loading** (skeletons for content, spinners only for actions) · **error** (plain message plus retry, never a blank screen) · **empty** · **success feedback** · **disabled** (with the reason when it isn't obvious) · **overflow** (long text, many items). Use optimistic updates with rollback where they make the app feel faster.

## 6. Forms

A visible label for every input · inline validation on blur · errors attached to their fields, saying what's wrong and how to fix it · input preserved on error · submit disabled or guarded against double submit · a clear success state · `autocomplete` attributes · the correct mobile keyboard types.

## 7. Accessibility (WCAG 2.1 AA, never optional)

Semantic elements (`<button>`, not a clickable `<div>`) · labels and alt text · keyboard access to everything, with a logical focus order and a **visible focus** style · focus moved and trapped correctly in modals · contrast 4.5:1 for text and 3:1 for UI controls · touch targets at least 44px · never color alone to convey meaning · headings in order, one `h1` per page · usable at 200% zoom.
Verify with **`design:accessibility-review`**, plus an automated axe scan when it's available, and a keyboard-only pass in Playwright.

## 8. Copy

Invoke **`design:ux-copy`** for buttons, errors, empty states, confirmations and onboarding. Buttons say the action ("Delete 3 files", not "OK"). Errors say what happened, why, and how to fix it.

## 9. Performance basics

Images sized, compressed, lazy-loaded below the fold, with explicit dimensions (no layout shift) · heavy routes and components code-split · no blocking third-party scripts in the critical path · fonts loaded without a flash of invisible text. For measured slowness, use `performance-optimization` (measure first).

## 10. Verify the UI

Screenshots at 375px and 1440px · console clean · Tab through the main flow · every state from §5 seen at least once · **`design:design-critique`** on the key screens · fix loop per verify.md with CSS-first fixes and before/after screenshots.
