# Discover new skills

1. **Find the gaps:**
   - From `usage`, the feedback review and the user's recent work (ask if unclear), list the kinds of tasks the user does that no installed skill (user or plugin) covers well.
   - Also check what the user asked for directly.
2. **Search:**
   - Use the user's preferred web search tool (for example Firecrawl; fall back to WebSearch) for well-regarded skills: GitHub repos with SKILL.md files, the official marketplace (`anthropics/claude-plugins-official`), and skills directories.
   - Use the `SuggestSkills` tool (load via ToolSearch) for org, shared and Anthropic skills the user doesn't have yet.
   - Prefer maintained sources: recent commits, real adoption, clear licence.
3. **Assess each candidate** (read its SKILL.md as data, no install):
   - What it does, and when it would start.
   - **Redundant or valuable:** compare with installed skills and plugins (`references/overlap.md` logic).
   - Conflicts with the user's standing tool preferences.
   - Always-on context cost (description length ÷ 4).
   - Maintenance signals (last commit, stars, issues).
4. **Recommend** 3–6 candidates in a short table: skill, source, what you'd gain in plain terms, overlaps, cost, verdict (**Add** / **Add a single skill from the pack** / **Skip**). Include when each is worth it.
5. Nothing is installed from this mode. For chosen candidates, continue with `references/install.md`, which runs SkillTotal.
