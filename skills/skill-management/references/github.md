# Publish to the public GitHub repo

Runs at the end of every run (shared rule 9) when `github_repo` is set in `config.json`, or when the user asks to publish.

## 1. Check whether there is anything to publish
Run `publish-repo` (without `--push`). It copies the skills listed in `github_repo.skills` into the local clone, replaces personal files (`reset_files`), applies the text generalizations (`sanitize`), scans for personal data (`forbidden`) and validates the skills. It stages the result but commits nothing.

- **`up to date`:** say "Your GitHub repo is already up to date" in one line and stop. Don't ask.
- **`blocked`:** tell the user what was found (personal data or validation errors) in plain English. Fix it (usually a new `sanitize` rule in config.json), then run step 1 again. Never publish while blocked.
- **`ready`:** continue.

Also report each `warnings` entry. A generalization that no longer applies means the local text changed; add or update the `sanitize` rule and rerun, so personal preferences don't leak into the public copy.

## 2. Ask the user
Use AskUserQuestion: "Update your GitHub repo (<remote>) with these changes?" List the changed skills and a one-line plain summary of what changed for people who download them. Options: "Yes, publish (Recommended)" and "Not now".

- **Not now:** leave the staged changes in the clone and say so. They'll be picked up next time.

## 3. On yes, publish it yourself
1. **Security scan:** run `mcp__skilltotal__scan_component` on `<clone>/skills`. If the scan is medium or high risk, show the findings and ask before continuing.
2. **README:** if a published skill gained, lost or changed a capability, update the matching section of `<clone>/README.md` so the public description stays accurate.
3. **Commit and push:** `publish-repo --push --message "<short summary of the change>"`. End the message with the commit attribution lines from the session's instructions, if any.
4. **Download zip (optional):** if the repo has releases, rebuild `claude-skills-v<next>.zip` from `<clone>/skills` next to the clone and offer to publish a release with `gh release create` (only if `gh auth status` shows the user is signed in; otherwise give the manual steps).
5. **Confirm:** report the commit, the repo link, and what changed, in plain English.

## Rules
- The published copy never contains personal paths, account names or personal tool preferences. `forbidden` is the last safety net, not the only one.
- Push only after the user's yes in this run. A yes in an earlier run doesn't count.
- If the push fails (for example, the sign-in expired), show the error and tell the user how to sign in again. Don't retry in a loop.
