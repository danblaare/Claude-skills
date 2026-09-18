"""Skills outside ~/.claude/skills (claude.ai account skills, Claude app plugins), where each skill
is available (Claude chat vs Claude Code), change tracking for them, and packaging for claude.ai upload."""
import datetime as dt
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

import core
from core import DISABLED, RUNS, SKILLS, frontmatter, log_event

# The Claude desktop app keeps a local copy of account skills and installed plugins here.
APP_ROOT = Path(os.environ.get("APPDATA", str(core.HOME / "AppData" / "Roaming"))) / "Claude" / "local-agent-mode-sessions"
REMOTE_STATE = core.STATE / "remote.json"
# Editable copies of claude.ai skills; the app's synced copy is overwritten on every sync.
CLAUDE_AI_SOURCES = core.BACKUPS / "claude-ai-sources"

CLAUDE_AI_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
RESERVED = ("anthropic", "claude")
CODE_ONLY_TOOLS = ("AskUserQuestion", "ToolSearch", "TaskStop", "PushNotification", "NotebookEdit", "Monitor",
                   "EnterPlanMode", "ExitPlanMode", "EnterWorktree")

ACTIVE, OFF, NONE = "✅", "⏸", "—"


def _ms_date(ms):
    return dt.datetime.fromtimestamp(ms / 1000).date().isoformat() if ms else None


def claude_ai_skills():
    """Account skills (yours and Anthropic's) as last synced by the desktop app."""
    manifests = sorted(APP_ROOT.glob("skills-plugin/*/*/manifest.json"), key=lambda p: p.stat().st_mtime)
    if not manifests:
        return {}, None
    mf = manifests[-1]
    data = json.loads(mf.read_text(encoding="utf-8"))
    out = {}
    for s in data.get("skills", []):
        out[s["name"]] = {
            "kind": "claude.ai",
            "creator": "you" if s.get("creatorType") == "user" else s.get("creatorType") or "unknown",
            "enabled": bool(s.get("enabled")),
            "updated": (s.get("updatedAt") or "")[:10] or None,
            "description": s.get("description", ""),
            "folder": str(mf.parent / "skills" / s["name"]),
        }
    listed = set(out)
    for d in sorted((mf.parent / "skills").iterdir()) if (mf.parent / "skills").is_dir() else []:
        if d.is_dir() and d.name not in listed and (d / "SKILL.md").is_file():
            fm = frontmatter((d / "SKILL.md").read_text(encoding="utf-8", errors="ignore")) or {}
            out[d.name] = {"kind": "app built-in", "creator": "anthropic", "enabled": True, "updated": None,
                           "description": str(fm.get("description", "")), "folder": str(d)}
    return out, _ms_date(data.get("lastUpdated"))


def app_plugins():
    """Plugins installed in the Claude app (work in chat, Cowork and Code sessions in the app)."""
    out = {}
    for mf in APP_ROOT.glob("*/*/rpm/manifest.json"):
        for p in json.loads(mf.read_text(encoding="utf-8")).get("plugins", []):
            skills_dir = mf.parent / p["id"] / "skills"
            skills = sorted(d.name for d in skills_dir.iterdir() if d.is_dir()) if skills_dir.is_dir() else []
            out[p["name"]] = {"kind": "plugin", "display": p.get("displayName", p["name"]),
                              "marketplace": p.get("marketplaceName", ""), "updated": (p.get("updatedAt") or "")[:10],
                              "skills": skills, "enabled": p.get("installationPreference") != "disabled",
                              "path": str(mf.parent / p["id"])}
    cli = core.HOME / ".claude" / "plugins" / "installed_plugins.json"
    if cli.exists():  # plugins installed through the Claude Code CLI: Code only
        data = json.loads(cli.read_text(encoding="utf-8"))
        for key, installs in (data.get("plugins") or {}).items():
            name = key.split("@")[0]
            path = Path((installs[0] if isinstance(installs, list) and installs else {}).get("installPath", ""))
            skills = sorted(d.name for d in (path / "skills").iterdir() if d.is_dir()) if (path / "skills").is_dir() else []
            out.setdefault(name, {"kind": "cli plugin", "display": name, "marketplace": key.split("@")[-1],
                                  "updated": "", "skills": skills, "enabled": True, "path": str(path)})
    return out


def local_skills():
    out = {n: {"kind": "local", "enabled": True, "folder": str(d)} for n, d in core.user_skills().items()}
    if DISABLED.is_dir():
        for d in DISABLED.iterdir():
            if (d / "SKILL.md").is_file():
                out[d.name] = {"kind": "local", "enabled": False, "folder": str(d)}
    return out


def availability():
    """One row per skill (plugins grouped) with where it is usable."""
    local, (cloud, synced_on), plugins = local_skills(), claude_ai_skills(), app_plugins()
    log = core.load_log()["skills"]
    rows = []
    for name, s in local.items():
        in_cloud = cloud.get(name)
        packaged = log.get(name, {}).get("packaged")
        chat = (f"{ACTIVE} uploaded" if in_cloud and in_cloud["enabled"] else
                f"{OFF} uploaded, off" if in_cloud else
                f"{NONE} not uploaded (package ready {packaged['date']})" if packaged else f"{NONE} not uploaded")
        code = f"{ACTIVE} local" if s["enabled"] else f"{OFF} local, disabled"
        rows.append({"key": name, "name": name, "kind": "local", "chat": chat, "code": code, "path": s["folder"],
                     "duplicate": bool(in_cloud and in_cloud["enabled"] and s["enabled"])})
    for name, s in cloud.items():
        if name in local:
            continue
        on = s["enabled"]
        label = "built into the Claude app" if s["kind"] == "app built-in" else "claude.ai account"
        rows.append({"key": f"claude.ai:{name}", "name": name, "kind": s["kind"], "path": s["folder"],
                     "chat": f"{ACTIVE} {label}" if on else f"{OFF} off in claude.ai",
                     "code": f"{ACTIVE} synced" if on else f"{OFF} off (synced)", "duplicate": False})
    for pname, p in plugins.items():
        both = p["kind"] == "plugin"
        n = len(p["skills"])
        rows.append({"key": f"plugin:{pname}", "name": f"{pname} plugin ({n} skill{'s' if n != 1 else ''})", "path": p["path"],
                     "kind": p["kind"], "skills": p["skills"],
                     "chat": (f"{ACTIVE} plugin" if p["enabled"] else f"{OFF} plugin off") if both else f"{NONE} Code-only plugin",
                     "code": f"{ACTIVE} plugin (desktop app)" if both else f"{ACTIVE} plugin (CLI)", "duplicate": False})
    return rows, synced_on


def cmd_where(_args):
    rows, synced_on = availability()
    print(json.dumps({"claude_ai_list_as_of": synced_on, "rows": rows}, indent=2, ensure_ascii=False))


def cmd_sync_remote(_args):
    """Record claude.ai and plugin changes in the skills log (first seen, updated, switched off/on, removed)."""
    cloud, synced_on = claude_ai_skills()
    plugins = app_plugins()
    current = {f"claude.ai:{n}": {"updated": s["updated"], "enabled": s["enabled"], "kind": s["kind"],
                                  "creator": s["creator"], "desc": s["description"]} for n, s in cloud.items()}
    current.update({f"plugin:{n}": {"updated": p["updated"], "enabled": p["enabled"], "kind": p["kind"],
                                    "skills": p["skills"], "marketplace": p["marketplace"]} for n, p in plugins.items()})
    first_run = not REMOTE_STATE.exists()
    previous = {} if first_run else json.loads(REMOTE_STATE.read_text(encoding="utf-8"))
    events = []
    for key, s in current.items():
        before = previous.get(key)
        source = (f"claude.ai ({'your skill' if s.get('creator') == 'you' else s.get('creator')})" if key.startswith("claude.ai:")
                  else f"Claude app plugin ({s.get('marketplace') or 'marketplace'})")
        if s["kind"] == "app built-in":
            source = "built into the Claude app"
        if before is None:
            # On the first sync the real install date is unknown; the last update date is the best bound.
            date = f"{s['updated'] or core.today()} (last update)" if first_run else core.today()
            n = len(s.get("skills", []))
            purpose = ((s.get("desc") or "")[:90] if key.startswith("claude.ai:")
                       else f"{n} skill{'s' if n != 1 else ''}: " + ", ".join(s["skills"]))
            log_event(key, "installed", date=date, source=source, purpose=purpose.split(". ")[0][:110])
            events.append((key, "first seen" if first_run else "added"))
            continue
        if s["updated"] and s["updated"] != before.get("updated"):
            what = "new version on claude.ai" if key.startswith("claude.ai:") else "new plugin version"
            added = sorted(set(s.get("skills", [])) - set(before.get("skills", [])))
            removed = sorted(set(before.get("skills", [])) - set(s.get("skills", [])))
            if added or removed:
                what += f" (skills added: {', '.join(added) or 'none'}; removed: {', '.join(removed) or 'none'})"
            log_event(key, "updated", date=s["updated"], summary=what, from_ref=before.get("updated"), to_ref=s["updated"])
            events.append((key, "updated"))
        if s["enabled"] != before.get("enabled", True):
            if s["enabled"]:
                log_event(key, "enabled", by="you (in the Claude app)")
            else:
                log_event(key, "disabled", reason="switched off in the Claude app")
            events.append((key, "enabled" if s["enabled"] else "switched off"))
    for key in set(previous) - set(current):
        log_event(key, "uninstalled", reason="removed from claude.ai / the Claude app (reason not recorded)")
        events.append((key, "removed"))
    core.STATE.mkdir(parents=True, exist_ok=True)
    REMOTE_STATE.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"claude_ai_list_as_of": synced_on, "first_run": first_run,
                      "changes": [{"skill": k, "change": c} for k, c in events if not first_run],
                      "tracked": len(current)}, indent=2, ensure_ascii=False))


# ---------- package for claude.ai ----------

def check_portability(folder):
    """Blockers (upload would fail) and warnings (won't behave the same in claude.ai chat)."""
    blockers, warnings, fixes = [], [], []
    text = (folder / "SKILL.md").read_text(encoding="utf-8")
    fm = frontmatter(text) or {}
    name, desc = str(fm.get("name", "")), str(fm.get("description", ""))
    extra = sorted(set(fm) - CLAUDE_AI_KEYS)
    if extra:
        fixes.append(f"frontmatter keys {extra} aren't allowed on claude.ai; the package moves them under metadata")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        blockers.append("name must be 1-64 lowercase letters, digits or hyphens")
    if any(r in name for r in RESERVED):
        blockers.append(f"name '{name}' contains a reserved word ({'/'.join(RESERVED)}); rename it before uploading")
    if not desc or len(desc) > 1024:
        blockers.append("description must be 1-1024 characters")
    if re.search(r"<[a-zA-Z/][^>]*>", desc):
        blockers.append("description contains XML/HTML-style tags, which claude.ai rejects")

    body = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in folder.rglob("*")
                     if p.is_file() and p.suffix in {".md", ".txt"})
    mcp = sorted(set(re.findall(r"mcp__([A-Za-z0-9_-]+?)__", body)))
    if mcp:
        warnings.append(f"uses MCP tools from {', '.join(mcp)}: works in chat only if the matching connectors are enabled on claude.ai")
    paths = sorted(set(re.findall(r"(?:~/\.claude[\w/.-]*|[A-Z]:\\\\?[\w\\ .-]+|\$HOME[\w/.-]*|%APPDATA%[\w\\.-]*)", body)))
    if paths:
        warnings.append(f"refers to files on this computer ({', '.join(paths[:4])}{'…' if len(paths) > 4 else ''}), which don't exist in chat")
    # Only count commands that look like commands (start of a line or inside backticks), not prose mentions.
    clis = re.findall(r"(?:^|`)\s*(?:git|npx|uvx|pip install|python|claude -p|bash|powershell)\b", body, re.M)
    if clis or (folder / "scripts").is_dir():
        warnings.append("runs scripts or command-line tools: in chat they run in a sandbox (if code execution is on) "
                        "without your local files, tools or logins")
    tools = [t for t in CODE_ONLY_TOOLS if t in body]
    if tools and "ask_user_input" in body:  # the skill already names chat's equivalent
        tools = [t for t in tools if t != "AskUserQuestion"]
    if tools:
        warnings.append(f"mentions Claude Code tools ({', '.join(tools)}) that chat doesn't have; Claude will improvise")
    if re.search(r"!`|\$ARGUMENTS|\$\{CLAUDE_", body):
        warnings.append("uses Claude Code-only features (dynamic context injection or $ARGUMENTS) that don't work in chat")
    if "context: fork" in text or "disable-model-invocation" in text:
        warnings.append("uses Claude Code-only frontmatter behaviour")
    verdict = "blocked" if blockers else "works with limits" if warnings else "ready"
    return {"verdict": verdict, "blockers": blockers, "warnings": warnings, "auto_fixes": fixes}


def cmd_pull_claude_ai(args):
    """Copy a claude.ai account skill from the app's synced copy into an editable source folder."""
    cloud, synced_on = claude_ai_skills()
    s = cloud.get(args.name)
    if not s or not (Path(s["folder"]) / "SKILL.md").is_file():
        raise SystemExit(json.dumps({"error": f"'{args.name}' isn't in the synced claude.ai skills (as of {synced_on})"}))
    dest = CLAUDE_AI_SOURCES / args.name
    if dest.exists() and not args.replace:
        raise SystemExit(json.dumps({"error": f"an editable copy already exists at {dest}; pass --replace to overwrite it"}))
    if dest.exists():
        archive = CLAUDE_AI_SOURCES / "_original" / f"{args.name}-replaced-{dt.datetime.now():%Y%m%d-%H%M%S}"
        shutil.move(str(dest), str(archive))
    shutil.copytree(s["folder"], dest)
    original = CLAUDE_AI_SOURCES / "_original" / f"{args.name}-{s['updated'] or core.today()}"
    if not original.exists():
        shutil.copytree(s["folder"], original)
    print(json.dumps({"editable_copy": str(dest), "original_kept": str(original), "claude_ai_list_as_of": synced_on,
                      "creator": s["creator"]}, indent=2))


def _package_source(name):
    """Active local skill first, then an editable claude.ai source copy, and a disabled skill only
    as a last resort. A disabled skill is out of use on purpose, so it must never silently beat an
    editable claude.ai copy: that shipped stale text over newer edits (2026-09-18).
    Returns (folder, log key, shadowed) where shadowed lists the candidates that were not used."""
    candidates = ((SKILLS / name, name),
                  (CLAUDE_AI_SOURCES / name, f"claude.ai:{name}"),
                  (DISABLED / name, name))
    found = [(folder, key) for folder, key in candidates if (folder / "SKILL.md").is_file()]
    if not found:
        raise SystemExit(json.dumps({"error": f"{name} is not a local skill or an editable claude.ai copy (see pull-claude-ai)"}))
    folder, key = found[0]
    return folder, key, [str(f) for f, _ in found[1:]]


def cmd_package(args):
    folder, log_key, shadowed = _package_source(args.name)
    report = check_portability(folder)
    if shadowed:
        report.setdefault("warnings", []).append(
            "this skill exists in more than one place: packaged " + str(folder)
            + "; ignored " + ", ".join(shadowed) + ". Check this is the copy you edited.")
    cloud, synced_on = claude_ai_skills()
    report["already_on_claude_ai"] = args.name in cloud
    if report["blockers"] and not args.force:
        print(json.dumps({"skill": args.name, "source": str(folder), **report, "package": None}, indent=2, ensure_ascii=False))
        return

    out_dir = RUNS / dt.datetime.now().strftime("%Y%m%d-%H%M%S") / "package"
    staged = out_dir / args.name
    shutil.copytree(folder, staged, ignore=shutil.ignore_patterns("__pycache__", ".git", "*.pyc"))
    sk = staged / "SKILL.md"
    text = sk.read_text(encoding="utf-8")
    fm = frontmatter(text) or {}
    extra = {k: fm[k] for k in fm if k not in CLAUDE_AI_KEYS}
    if extra:  # rewrite frontmatter with only allowed keys; keep the rest under metadata
        keep = {k: fm[k] for k in fm if k in CLAUDE_AI_KEYS}
        meta = dict(keep.get("metadata") or {})
        meta.update({k: str(v) for k, v in extra.items()})
        keep["metadata"] = meta
        lines = [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in keep.items()]
        text = re.sub(r"^---\r?\n.*?\r?\n---", "---\n" + "\n".join(lines) + "\n---", text, count=1, flags=re.S)
        sk.write_text(text, encoding="utf-8")
    zpath = out_dir / f"{args.name}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in staged.rglob("*"):
            if f.is_file():
                z.write(f, Path(args.name) / f.relative_to(staged))
    copies = [str(zpath)]
    export_dir = core.load_config().get("export_dir")
    if export_dir and Path(export_dir).is_dir():
        dest = Path(export_dir) / "claude.ai packages"
        dest.mkdir(exist_ok=True)
        shutil.copy2(zpath, dest / zpath.name)
        copies.append(str(dest / zpath.name))
    log = core.load_log()
    entry = log["skills"].setdefault(log_key, {"purpose": "", "source": "", "status": "active", "installed": None,
                                               "modifications": [], "updates": [], "uninstalled": None})
    entry["packaged"] = {"date": core.today(), "file": copies[-1], "verdict": report["verdict"]}
    core.save_log(log)
    print(json.dumps({"skill": args.name, "source": str(folder), **report, "package": copies,
                      "size_kb": round(zpath.stat().st_size / 1024, 1),
                      "claude_ai_list_as_of": synced_on}, indent=2, ensure_ascii=False))
