"""Health checks, context-cost estimates and live trigger tests."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import core
from core import DISABLED, SKILLS, frontmatter

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
# Relative file references such as `references/x.md`, (scripts/y.py), ../../z.md
REF_RE = re.compile(r"[`(\s](\.{0,2}/?(?:[\w.-]+/)*[\w.-]+\.(?:md|py|sh|js|ts|json|yaml|yml|txt|csv|html))[`)\s]")
KNOWN_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "model", "version",
              "disable-model-invocation", "user-invocable", "argument-hint", "when_to_use", "context", "agent"}


def tokens(chars):
    return round(chars / 4)


def validate_skill(folder):
    issues = []

    def add(level, msg):
        issues.append({"level": level, "issue": msg})

    sk = folder / "SKILL.md"
    if not sk.is_file():
        add("error", "SKILL.md missing, so Claude can't load this skill")
        return issues
    try:
        text = sk.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        add("error", "SKILL.md is not valid UTF-8")
        return issues
    try:
        fm = frontmatter(text)
    except Exception as e:
        add("error", f"frontmatter doesn't parse ({str(e).splitlines()[0]}), so the skill won't load")
        return issues
    if not isinstance(fm, dict):
        add("error", "no frontmatter block (--- name/description ---)")
        return issues
    name, desc = fm.get("name"), str(fm.get("description") or "")
    if not name:
        add("error", "frontmatter has no name")
    elif name != folder.name:
        add("warn", f"name '{name}' differs from folder '{folder.name}'")
    elif not NAME_RE.match(str(name)):
        add("warn", "name should be lowercase letters, digits and hyphens (max 64)")
    if not desc:
        add("error", "no description, so Claude can't tell when to use it")
    elif len(desc) > 1024:
        add("error", f"description is {len(desc)} characters (limit 1024) and may be rejected or cut")
    elif not re.search(r"\b(use|when|whenever|trigger)\b", desc, re.I):
        add("info", "description doesn't say when to use the skill; auto-triggering may be unreliable")
    for key in set(fm) - KNOWN_KEYS:
        add("info", f"unrecognised frontmatter key '{key}'")

    body_lines = text.count("\n")
    if body_lines > 500:
        add("info", f"SKILL.md is {body_lines} lines; consider moving detail into references/ files")
    for ref in sorted(set(REF_RE.findall(" " + text + " "))):
        # Bare filenames are usually examples ("PERF.md"); only check path-like references.
        if ref.startswith(("http", "www.")) or "*" in ref or "<" in ref or "/" not in ref:
            continue
        if not (folder / ref).exists() and not (folder / ref.lstrip("./")).exists():
            add("warn", f"references '{ref}', which doesn't exist in the skill folder")
    for f in folder.rglob("*"):
        if f.is_dir() and f.name == "__pycache__":
            add("info", f"cache folder {f.relative_to(folder)} can be deleted")
        elif f.is_file() and f.suffix in {".md", ".py", ".json", ".txt", ".yaml", ".yml"}:
            try:
                f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                add("warn", f"{f.relative_to(folder)} is not UTF-8")
    return issues


def cmd_validate(args):
    targets = {}
    if args.path:
        targets[Path(args.path).name] = Path(args.path)
    else:
        targets.update({n: d for n, d in core.user_skills().items() if not args.name or n in args.name})
    report = {n: validate_skill(d) for n, d in targets.items()}

    cross = []
    if not args.path and not args.name:
        installed = set(core.user_skills())
        disabled = {d.name for d in DISABLED.iterdir()} if DISABLED.is_dir() else set()
        for e in core.load_manifest()["skills"]:
            if e["name"] not in installed | disabled:
                cross.append({"level": "warn", "issue": f"manifest tracks '{e['name']}' but it isn't installed"})
        log = core.load_log()["skills"]
        for n in installed - set(log):
            cross.append({"level": "warn", "issue": f"'{n}' is installed but missing from the skills log"})
        for n, s in log.items():
            if ":" in n:
                continue  # claude.ai skills and app plugins have no folder here; `sync-remote` tracks them
            if s["status"] == "active" and n not in installed:
                cross.append({"level": "warn", "issue": f"log says '{n}' is active but its folder is gone"})
            if s["status"] == "disabled" and n not in disabled:
                cross.append({"level": "warn", "issue": f"log says '{n}' is disabled but no disabled copy exists"})
    counts = {lvl: sum(1 for v in list(report.values()) + [cross] for i in v if i["level"] == lvl)
              for lvl in ("error", "warn", "info")}
    print(json.dumps({"summary": counts, "skills": report, "cross_checks": cross}, indent=2, ensure_ascii=False))


def skill_cost(folder):
    text = (folder / "SKILL.md").read_text(encoding="utf-8")
    fm = frontmatter(text) or {}
    always = len(str(fm.get("name", ""))) + len(str(fm.get("description", ""))) + 20
    extra = sum(len(f.read_text(encoding="utf-8", errors="ignore")) for f in folder.rglob("*")
                if f.is_file() and f.name != "SKILL.md" and f.suffix in {".md", ".txt", ".json", ".yaml", ".yml"})
    return {"always_on_tokens": tokens(always), "on_use_tokens": tokens(len(text)), "reference_tokens_max": tokens(extra)}


def cmd_cost(_args):
    rows = {n: skill_cost(d) for n, d in core.user_skills().items()}
    total = sum(r["always_on_tokens"] for r in rows.values())
    print(json.dumps({"note": "estimates at ~4 characters per token; always-on = paid in every session",
                      "total_always_on_tokens": total,
                      "skills": dict(sorted(rows.items(), key=lambda kv: -kv[1]["on_use_tokens"]))}, indent=2))


def cmd_trigger_test(args):
    exe = shutil.which("claude")
    if not exe:
        raise SystemExit(json.dumps({"error": "claude CLI not found on PATH"}))
    core.TRIGGER_TEST_DIR.mkdir(parents=True, exist_ok=True)
    blocked = "Bash,PowerShell,Write,Edit,MultiEdit,NotebookEdit,WebFetch,WebSearch,Agent,Task"
    results, total_cost = [], 0.0
    for prompt in args.prompt:
        cmd = [exe, "-p", prompt, "--output-format", "stream-json", "--verbose",
               "--max-turns", str(args.max_turns), "--disallowedTools", blocked]
        try:
            proc = subprocess.run(cmd, cwd=core.TRIGGER_TEST_DIR, capture_output=True, text=True,
                                  encoding="utf-8", timeout=args.timeout)
            out = proc.stdout
        except subprocess.TimeoutExpired as e:
            out = e.stdout or ""
        skills, reads, cost = [], [], None
        for line in out.splitlines():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") == "assistant":
                for c in d["message"].get("content", []):
                    if c.get("type") != "tool_use":
                        continue
                    if c["name"] == "Skill":
                        skills.append(str(c["input"].get("skill")))
                    elif c["name"] == "Read" and str(c["input"].get("file_path", "")).replace("\\", "/").endswith("/SKILL.md"):
                        reads.append(Path(c["input"]["file_path"]).parent.name)
            elif d.get("type") == "result":
                cost = d.get("total_cost_usd")
        triggered = skills + [r for r in reads if r not in skills]
        total_cost += cost or 0
        row = {"prompt": prompt, "triggered": triggered or ["(none)"], "cost_usd": cost}
        if args.expect:
            row["pass"] = (args.expect in [t.split(":")[-1] for t in triggered]) != args.expect_not
        results.append(row)
    print(json.dumps({"results": results, "total_cost_usd": round(total_cost, 4),
                      "expect": args.expect, "mode": "should NOT trigger" if args.expect_not else "should trigger"},
                     indent=2, ensure_ascii=False))
