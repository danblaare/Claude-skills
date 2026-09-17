"""Publish selected skills to the user's public GitHub repo: copy, strip personal settings, check for
personal data, validate, then (only when asked) commit and push.

Settings live under `github_repo` in config.json:
  path        local clone of the repo
  remote      repo URL (for messages)
  skills      skill folder names to publish
  author      {"name", "email"} used for commits
  reset_files {"<skill>/<file>": <JSON content written instead of the local file>}
  sanitize    [{"file": "<skill>/<file>", "find": "...", "replace": "..."}] text generalizations
  forbidden   strings that must never appear in the published skills (personal data)
"""
import json
import shutil
import subprocess
from pathlib import Path

import core
import health
from core import SKILLS


def _settings():
    cfg = core.load_config().get("github_repo") or {}
    if not cfg.get("path") or not cfg.get("skills"):
        raise SystemExit(json.dumps({"error": "github_repo is not configured in config.json"}))
    repo = Path(cfg["path"])
    if not (repo / ".git").is_dir():
        raise SystemExit(json.dumps({"error": f"not a git clone: {repo}"}))
    return cfg, repo


def _git(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout + r.stderr).strip()


def sync(cfg, repo):
    """Copy the skills into the clone and apply resets and generalizations. Returns problems found."""
    unapplied = []
    for name in cfg["skills"]:
        src, dest = SKILLS / name, repo / "skills" / name
        if not (src / "SKILL.md").is_file():
            unapplied.append(f"skill not installed: {name}")
            continue
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    for rel, content in (cfg.get("reset_files") or {}).items():
        f = repo / "skills" / rel
        if f.parent.is_dir():
            f.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for rule in cfg.get("sanitize") or []:
        f = repo / "skills" / rule["file"]
        text = f.read_text(encoding="utf-8") if f.is_file() else ""
        if rule["find"] in text:
            f.write_text(text.replace(rule["find"], rule["replace"]), encoding="utf-8")
        else:
            unapplied.append(f"generalization not applied (text changed?): {rule['file']}: {rule['find'][:60]}")

    leaks = []
    for f in (repo / "skills").rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="ignore").lower()
            leaks += [f"{f.relative_to(repo).as_posix()}: '{w}'" for w in cfg.get("forbidden") or [] if w.lower() in text]

    issues = []
    for name in cfg["skills"]:
        if (repo / "skills" / name).is_dir():
            issues += [f"{name}: {i['issue']}" for i in health.validate_skill(repo / "skills" / name) if i["level"] == "error"]
    return unapplied, leaks, issues


def cmd_publish_repo(args):
    cfg, repo = _settings()
    unapplied, leaks, issues = sync(cfg, repo)
    _git(repo, "add", "-A")
    _, changed = _git(repo, "status", "--porcelain")
    result = {"repo": str(repo), "remote": cfg.get("remote"), "changed": changed.splitlines(),
              "personal_data_found": leaks, "validation_errors": issues, "warnings": unapplied}

    blocked = leaks or issues
    if not changed:
        result["status"] = "up to date: nothing to publish"
    elif blocked:
        result["status"] = "blocked: fix personal data or validation errors first (nothing committed)"
    elif not args.push:
        result["status"] = "ready: changes staged in the local clone, not committed (rerun with --push)"
    else:
        author = cfg.get("author") or {}
        who = ["-c", f"user.name={author['name']}", "-c", f"user.email={author['email']}"] if author else []
        message = args.message or "Update skills"
        code, out = _git(repo, *who, "commit", "-m", message)
        if code:
            result["status"] = f"commit failed: {out}"
        else:
            code, out = _git(repo, "push", "origin", "HEAD")
            result["status"] = "pushed" if code == 0 else f"push failed: {out}"
            _, result["commit"] = _git(repo, "log", "-1", "--oneline")
    print(json.dumps(result, indent=2, ensure_ascii=False))
