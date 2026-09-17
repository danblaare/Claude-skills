#!/usr/bin/env python3
"""Core helpers for skill-management: paths, config, manifest, backups, update check,
change detection against the last baseline, transcript access, and the skills log.

The CLI lives in skillmgr.py.
"""
import argparse
import datetime as dt
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOME = Path.home()
SKILLS = HOME / ".claude" / "skills"
BACKUPS = HOME / ".claude" / "skill-backups"
RUNS = BACKUPS / "runs"
MANIFEST = Path(__file__).resolve().parent.parent / "manifest.json"
STATE = BACKUPS / "state"
SNAPSHOT = STATE / "snapshot"
SNAPSHOT_INDEX = STATE / "snapshot.json"
LOG = BACKUPS / "skills-log.json"
TRANSCRIPTS = HOME / ".claude" / "projects"
DISABLED = BACKUPS / "disabled"
CONFIG = Path(__file__).resolve().parent.parent / "config.json"
# Sessions started by the trigger tester run from this folder; keep them out of usage stats.
TRIGGER_TEST_DIR = BACKUPS / "trigger-tests"
SELF = Path(__file__).resolve().parent.parent.name
# Files this skill rewrites itself; changes to them are bookkeeping, not customizations.
IGNORED = {(SELF, "manifest.json"), (SELF, "config.json")}
EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(data):
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(*args, cwd=None, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r


def frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return None
    try:
        import yaml
        return yaml.safe_load(m.group(1))
    except ImportError:
        out = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip('"')
        return out


def apply_patches(root, patches):
    """Re-apply local customizations. Returns a list of human-readable notes."""
    notes = []
    for p in patches:
        f = root / p["file"]
        if not f.exists():
            notes.append(f"patch skipped, file missing upstream: {p['file']}")
            continue
        text = f.read_text(encoding="utf-8")
        if p["type"] == "replace_text":
            if p["find"] not in text:
                notes.append(f"replace_text '{p['find']}' not found in {p['file']} (upstream may have changed it)")
            text = text.replace(p["find"], p["replace"])
        elif p["type"] == "frontmatter_description":
            new_line = "description: " + json.dumps(p["value"], ensure_ascii=False)
            text, n = re.subn(r"(?m)^description:.*$", lambda _: new_line, text, count=1)
            if n == 0:
                notes.append(f"no description line found in {p['file']}")
        else:
            notes.append(f"unknown patch type {p['type']}")
            continue
        f.write_text(text, encoding="utf-8", newline="")
    return notes


def materialize(clone, commit, entry, dest):
    """Write the entry's tracked files at `commit` into dest, then apply patches."""
    dest.mkdir(parents=True, exist_ok=True)
    missing = []
    for local, upstream in entry["files"].items():
        r = git("show", f"{commit}:{upstream}", cwd=clone, check=False)
        if r.returncode != 0:
            missing.append(upstream)
            continue
        out = dest / local
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(r.stdout, encoding="utf-8", newline="")
    notes = apply_patches(dest, entry.get("local_patches", []))
    return missing, notes


def tree_equal(a, b, files):
    for local in files:
        fa, fb = a / local, b / local
        if fa.exists() != fb.exists():
            return False
        if fa.exists() and fa.read_bytes().replace(b"\r\n", b"\n") != fb.read_bytes().replace(b"\r\n", b"\n"):
            return False
    return True


def today():
    return dt.date.today().isoformat()


def user_skills():
    return {d.name: d for d in sorted(SKILLS.iterdir()) if (d / "SKILL.md").is_file()} if SKILLS.is_dir() else {}


def file_hashes(folder):
    out = {}
    for f in sorted(folder.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts:
            rel = f.relative_to(folder).as_posix()
            if (folder.name, rel) not in IGNORED:
                out[rel] = hashlib.sha256(f.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return out


def read_text(f):
    try:
        return f.read_text(encoding="utf-8").splitlines(keepends=True)
    except (UnicodeDecodeError, FileNotFoundError):
        return []


def transcript_events(since=None):
    """Yield (timestamp, session, tool_name, input) for tool calls in Claude Code transcripts."""
    if not TRANSCRIPTS.is_dir():
        return
    since_ts = since.timestamp() if since else 0
    for jf in TRANSCRIPTS.glob("*/*.jsonl"):
        if "trigger-tests" in jf.parent.name or jf.stat().st_mtime < since_ts:
            continue
        with open(jf, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"tool_use"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = d.get("timestamp", "")
                if since and ts and ts < since.isoformat():
                    continue
                content = (d.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                for it in content:
                    if isinstance(it, dict) and it.get("type") == "tool_use":
                        yield ts, d.get("sessionId", jf.stem), it.get("name"), it.get("input") or {}


def claude_touches(name, since):
    """Best-effort: Claude tool calls since `since` that wrote to or ran shell commands on a skill folder."""
    needle = f".claude/skills/{name}".lower()
    hits = []
    for ts, session, tool, inp in transcript_events(since):
        if tool in EDIT_TOOLS:
            path = str(inp.get("file_path") or inp.get("notebook_path") or "").replace("\\", "/").lower()
            if needle in path:
                hits.append({"timestamp": ts, "session": session, "tool": tool, "target": path.split("/skills/", 1)[-1]})
        elif tool in SHELL_TOOLS:
            cmd = str(inp.get("command", "")).replace("\\", "/").lower()
            cmd = cmd.replace(f"{SELF}/scripts/skillmgr.py", "")  # running the helper is not an edit
            if name.lower() in cmd and ".claude/skills" in cmd:
                hits.append({"timestamp": ts, "session": session, "tool": tool, "target": cmd[:160]})
    return sorted(hits, key=lambda h: h["timestamp"])


def take_snapshot(names=None):
    STATE.mkdir(parents=True, exist_ok=True)
    index = json.loads(SNAPSHOT_INDEX.read_text(encoding="utf-8")) if SNAPSHOT_INDEX.exists() else {"skills": {}}
    current = user_skills()
    targets = names or list(current) + [n for n in index["skills"] if n not in current]
    for name in targets:
        dest = SNAPSHOT / name
        if dest.exists():
            shutil.rmtree(dest)
        if name in current:
            shutil.copytree(current[name], dest, ignore=shutil.ignore_patterns("__pycache__"))
            index["skills"][name] = {"files": file_hashes(current[name])}
        else:
            index["skills"].pop(name, None)
    index["taken_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    SNAPSHOT_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def cmd_snapshot(args):
    index = take_snapshot(getattr(args, "name", None) or None)
    print(json.dumps({"taken_at": index["taken_at"], "skills": sorted(index["skills"])}, indent=2))


def cmd_changes(_args):
    if not SNAPSHOT_INDEX.exists():
        print(json.dumps({"baseline": False, "note": "No snapshot yet; run `snapshot` at the end of this assessment."}))
        return
    index = json.loads(SNAPSHOT_INDEX.read_text(encoding="utf-8"))
    since = dt.datetime.fromisoformat(index["taken_at"])
    out_dir = RUNS / dt.datetime.now().strftime("%Y%m%d-%H%M%S") / "changes"
    current, previous = user_skills(), index["skills"]
    report = {"baseline": True, "since": index["taken_at"], "installed": [], "uninstalled": [], "modified": []}

    for name in sorted(set(current) - set(previous)):
        report["installed"].append({"name": name, "folder": str(current[name]),
                                    "claude_activity": claude_touches(name, since)})
    for name in sorted(set(previous) - set(current)):
        report["uninstalled"].append({"name": name, "claude_activity": claude_touches(name, since)})
    for name in sorted(set(current) & set(previous)):
        now, before = file_hashes(current[name]), previous[name]["files"]
        changed = sorted(f for f in set(now) | set(before) if now.get(f) != before.get(f))
        if not changed:
            continue
        diff = []
        for rel in changed:
            diff += difflib.unified_diff(read_text(SNAPSHOT / name / rel), read_text(current[name] / rel),
                                         f"before/{name}/{rel}", f"now/{name}/{rel}")
        out_dir.mkdir(parents=True, exist_ok=True)
        diff_file = out_dir / f"{name}.diff"
        diff_file.write_text("".join(diff), encoding="utf-8")
        mtimes = [(current[name] / f).stat().st_mtime for f in changed if (current[name] / f).exists()]
        activity = claude_touches(name, since)
        report["modified"].append({
            "name": name,
            "files": [{"file": f, "change": "added" if f not in before else "deleted" if f not in now else "edited"}
                      for f in changed],
            "last_modified": dt.datetime.fromtimestamp(max(mtimes)).date().isoformat() if mtimes else today(),
            "diff_file": str(diff_file),
            "diff_lines": len(diff),
            "likely_author": "Claude" if activity else "you (no matching Claude session found)",
            "claude_activity": activity[-10:],
        })
    print(json.dumps(report, indent=2, ensure_ascii=False))


def load_log():
    return json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {"skills": {}}


def save_log(log):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def log_event(skill, kind, date=None, by=None, summary=None, source=None, purpose=None, reason=None,
              from_ref=None, to_ref=None, rationale=None):
    log = load_log()
    s = log["skills"].setdefault(skill, {"purpose": "", "source": "", "status": "active", "installed": None,
                                         "modifications": [], "updates": [], "uninstalled": None})
    date = date or today()
    if purpose:
        s["purpose"] = purpose
    if source:
        s["source"] = source
    why = {"rationale": rationale} if rationale else {}
    if kind == "installed":
        s.update(status="active", installed=date, uninstalled=None)
    elif kind == "modified":
        s["modifications"].append({"date": date, "by": by or "unknown", "summary": summary or "", **why})
    elif kind == "updated":
        s["updates"].append({"date": date, "from": from_ref, "to": to_ref, "summary": summary or "", **why})
    elif kind == "rationale":
        # Attach the user's rationale to the most recent edit or update (e.g. one logged by sync-remote or apply).
        latest = max(s["modifications"] + s["updates"], key=lambda e: (e["date"], "rationale" not in e), default=None)
        if latest is None:
            raise SystemExit(f"no edit or update logged for {skill} to attach a rationale to")
        latest["rationale"] = rationale or "no rationale given"
    elif kind == "uninstalled":
        s.update(status="uninstalled", disabled=None,
                 uninstalled={"date": date, "reason": reason or "no reason given"})
    elif kind == "disabled":
        s.update(status="disabled", disabled={"date": date, "reason": reason or "no reason given"})
    elif kind == "enabled":
        s.update(status="active", disabled=None)
        s["modifications"].append({"date": date, "by": by or "you", "summary": "Re-enabled"})
    elif kind == "restored":
        s.update(status="active", uninstalled=None, disabled=None)
        s["modifications"].append({"date": date, "by": by or "rollback", "summary": summary or "Restored from backup", **why})
    save_log(log)
    return s


def log_rows():
    """Merge the history log with live availability (local, claude.ai, plugins) into display rows."""
    import remote  # local import: remote depends on core
    log = load_log()["skills"]
    avail, synced_on = remote.availability()
    by_key = {r["key"]: r for r in avail}
    kind_order = {"local": 0, "claude.ai": 1, "app built-in": 2, "plugin": 3, "cli plugin": 3}
    rows = []
    for key in set(log) | set(by_key):
        s = log.get(key, {"purpose": "", "source": "", "status": "active", "installed": None,
                          "modifications": [], "updates": [], "uninstalled": None})
        a = by_key.get(key)
        if a:
            kind, chat, code, name = a["kind"], a["chat"], a["code"], a["name"]
        else:  # only in history: removed
            kind = "plugin" if key.startswith("plugin:") else "claude.ai" if key.startswith("claude.ai:") else "local"
            chat = "—" if kind == "local" else "✗ removed"
            code = "✗ uninstalled" if kind == "local" else "✗ removed"
            name = key.split(":", 1)[-1] + (" plugin" if kind == "plugin" else "")
        rows.append({"key": key, "name": name, "kind": kind, "chat": chat, "code": code, "log": s,
                     "duplicate": bool(a and a.get("duplicate")), "removed": a is None,
                     "sort": (a is None, kind_order.get(kind, 4), name)})
    return sorted(rows, key=lambda r: r["sort"]), synced_on


def cmd_log(args):
    if args.log_cmd == "event":
        print(json.dumps(log_event(args.skill, args.type, args.date, args.by, args.summary, args.source,
                                   args.purpose, args.reason, args.from_ref, args.to_ref, args.rationale), indent=2, ensure_ascii=False))
        return

    import remote  # local import: remote depends on core
    print(render_log_tables(*log_rows(), remote.claude_ai_skills()[0], remote.app_plugins()))


def _short(text, limit=80):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _history(s):
    """One date-sorted list of everything that happened to a skill, newest first."""
    why = lambda e: f" — why: {e['rationale']}" if e.get("rationale") else ""
    events = [(m["date"], f"edited by {m['by']}: {m['summary']}{why(m)}") for m in s.get("modifications", [])]
    events += [(u["date"], f"updated: {u['summary']}{why(u)}") for u in s.get("updates", [])]
    if s.get("packaged"):
        events.append((s["packaged"]["date"], "packaged for claude.ai upload"))
    if s.get("disabled"):
        events.append((s["disabled"]["date"], f"disabled: {s['disabled']['reason']}"))
    if s.get("uninstalled"):
        events.append((s["uninstalled"]["date"], f"uninstalled: {s['uninstalled']['reason']}"))
    events.sort(key=lambda e: e[0], reverse=True)
    return "<br>".join(f"{d} · {t}" for d, t in events) if events else "—"


def render_log_tables(rows, synced_on, cloud, plugins):
    local = [r for r in rows if r["kind"] == "local"]
    remote_rows = [r for r in rows if r["kind"] != "local"]
    out = []

    out += ["### Local skills: Claude Code on this computer only", "",
            "| Skill | Status | Used for | Source | Installed | History (newest first) |",
            "|---|---|---|---|---|---|"]
    order = {"active": 0, "disabled": 1, "uninstalled": 2}
    for r in sorted(local, key=lambda r: (order.get(r["log"].get("status"), 3), r["name"])):
        s = r["log"]
        if r["removed"]:
            status = "✗ uninstalled"
        elif r["code"].startswith("⏸"):
            status = "⏸ disabled"
        else:
            status = "✅ active"
        if r["chat"].startswith("✅"):
            status += "<br>⚠ also on claude.ai (loaded twice in Code)" if r["duplicate"] else "<br>also on claude.ai"
        source = s.get("source") or "—"
        source = ("yours" if source.startswith("own") else
                  "GitHub: " + source.split("GitHub ", 1)[1].split("@")[0] if source.startswith("GitHub ") else source)
        out.append(f"| {r['name']} | {status} | {_short(s.get('purpose')) or '—'} | {source} | "
                   f"{s.get('installed') or 'unknown'} | {_history(s)} |")

    is_plugin = lambda r: r["kind"] in ("plugin", "cli plugin")
    remote_status = lambda r: "✗ removed" if r["removed"] else "✅ on" if r["chat"].startswith("✅") else "⏸ off"

    out += ["", "### claude.ai skills: Claude chat and Claude Code", "",
            "| Skill | Type | Status | Used for | Last updated | History (newest first) |",
            "|---|---|---|---|---|---|"]

    def skill_key(r):
        name = r["key"].split(":", 1)[-1]
        group = 0 if cloud.get(name, {}).get("creator") == "you" else 1 if r["kind"] == "claude.ai" else 2
        return (r["removed"], group, name)

    for r in sorted((r for r in remote_rows if not is_plugin(r)), key=skill_key):
        s, name = r["log"], r["key"].split(":", 1)[-1]
        c = cloud.get(name, {})
        kind = ("yours" if c.get("creator") == "you" else "built into the app" if r["kind"] == "app built-in"
                else "Anthropic")
        used_for = _short(s.get("purpose") or c.get("description")) or "—"
        out.append(f"| {name} | {kind} | {remote_status(r)} | {used_for} | {c.get('updated') or '—'} | {_history(s)} |")

    out += ["", "### App plugins: Claude chat and Claude Code", "",
            "| Plugin | Skills | Status | Includes | Last updated | History (newest first) |",
            "|---|---|---|---|---|---|"]
    for r in sorted((r for r in remote_rows if is_plugin(r)), key=lambda r: (r["removed"], r["key"])):
        s, name = r["log"], r["key"].split(":", 1)[-1]
        p = plugins.get(name, {})
        count = str(len(p.get("skills", []))) + (" (Code only)" if r["kind"] == "cli plugin" else "")
        includes = _short(", ".join(p.get("skills", [])), 110) or "—"
        out.append(f"| {name} | {count} | {remote_status(r)} | {includes} | {p.get('updated') or '—'} | {_history(s)} |")

    out += ["", f"claude.ai list as of {synced_on or 'unknown'}, from the Claude desktop app's synced copy "
                f"(open the app to refresh it)."]
    return "\n".join(line.replace("\n", " ") for line in out)


def cmd_inventory(args):
    rows = []
    tracked = {e["name"]: e for e in load_manifest()["skills"]}
    for base, scope in [(SKILLS, "user"), (Path.cwd() / ".claude" / "skills", "project"), (DISABLED, "disabled")]:
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            sk = d / "SKILL.md"
            if not sk.is_file():
                continue
            fm = frontmatter(sk.read_text(encoding="utf-8")) or {}
            rows.append({
                "scope": scope,
                "name": fm.get("name", d.name),
                "folder": str(d),
                "description": str(fm.get("description", "")) if getattr(args, "full", False) else str(fm.get("description", ""))[:160],
                "tracked_source": tracked[d.name]["repo"] if d.name in tracked else None,
            })
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def make_backup(keep=None, label="skills"):
    """Zip ~/.claude/skills (paths stored as skills/<name>/...) and prune to the newest `keep`."""
    keep = keep or load_config().get("keep_backups", 8)
    BACKUPS.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    zpath = BACKUPS / f"{label}-{stamp}.zip"
    count = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in SKILLS.rglob("*"):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, f.relative_to(SKILLS.parent))
                count += 1
    zips = sorted(BACKUPS.glob("skills-*.zip"))
    pruned = []
    for old in zips[:-keep] if len(zips) > keep else []:
        old.unlink()
        pruned.append(old.name)
    return {"backup": str(zpath), "files": count, "pruned": pruned}


def cmd_backup(args):
    print(json.dumps(make_backup(args.keep), indent=2))


def cmd_check(_args):
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run = RUNS / stamp
    run.mkdir(parents=True, exist_ok=True)
    results = []
    for entry in load_manifest()["skills"]:
        name = entry["name"]
        res = {"name": name, "repo": entry["repo"], "installed_commit": entry["installed_commit"]}
        if not (SKILLS / name).is_dir():
            res["status"] = "disabled" if (DISABLED / name).is_dir() else "not_installed"
            results.append(res)
            continue
        try:
            with tempfile.TemporaryDirectory() as tmp:
                clone = Path(tmp) / "repo"
                git("clone", "--quiet", "--filter=blob:none", "--no-checkout",
                    "--branch", entry.get("branch", "main"), entry["repo"], str(clone))
                paths = list(entry["files"].values())
                latest = git("rev-parse", "HEAD", cwd=clone).stdout.strip()
                res["latest_commit"] = latest

                # Detect manual edits: installed files vs (installed commit + patches).
                expected = run / "expected" / name
                materialize(clone, entry["installed_commit"], entry, expected)
                res["local_drift"] = not tree_equal(expected, SKILLS / name, entry["files"])

                # Compare file contents, not commit ids: most upstream commits don't touch these files.
                diff = git("diff", entry["installed_commit"], latest, "--", *paths, cwd=clone).stdout
                if git("show", f"{latest}:{paths[0]}", cwd=clone, check=False).returncode != 0:
                    res["status"] = "removed_upstream"
                elif not diff.strip():
                    res["status"] = "up_to_date"
                else:
                    log = git("log", "--format=%h %ad %s", "--date=short",
                              f"{entry['installed_commit']}..{latest}", "--", *paths, cwd=clone).stdout
                    (run / "diffs").mkdir(exist_ok=True)
                    diff_file = run / "diffs" / f"{name}.diff"
                    diff_file.write_text(diff, encoding="utf-8")
                    staged = run / "staged" / name
                    missing, notes = materialize(clone, latest, entry, staged)
                    sk = staged / "SKILL.md"
                    fm = frontmatter(sk.read_text(encoding="utf-8")) if sk.exists() else None
                    res.update({
                        "status": "update_available",
                        "commits": log.strip().splitlines(),
                        "diff_file": str(diff_file),
                        "diff_lines": len(diff.splitlines()),
                        "staged_dir": str(staged),
                        "installed_dir": str(SKILLS / name),
                        "missing_upstream_files": missing,
                        "patch_notes": notes,
                        "frontmatter_valid": bool(fm and fm.get("name") and fm.get("description")),
                    })
        except Exception as e:  # report and continue with the next skill
            res["status"] = "error"
            res["error"] = str(e)
        results.append(res)
    summary = {"run_dir": str(run), "results": results}
    (run / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def cmd_apply(args):
    run = Path(args.run)
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    res = next((r for r in summary["results"] if r["name"] == args.name), None)
    if not res or res.get("status") != "update_available":
        sys.exit(f"{args.name}: no staged update in {run}")
    if not res.get("frontmatter_valid"):
        sys.exit(f"{args.name}: staged SKILL.md frontmatter invalid; refusing to install")
    if not sorted(BACKUPS.glob("skills-*.zip")):
        sys.exit("no backup found; run `backup` first")

    manifest = load_manifest()
    entry = next(e for e in manifest["skills"] if e["name"] == args.name)
    staged, target = Path(res["staged_dir"]), SKILLS / args.name
    for local in entry["files"]:
        src, dst = staged / local, target / local
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif dst.exists():
            dst.unlink()  # file removed upstream
    old_commit = entry["installed_commit"]
    entry["installed_commit"] = res["latest_commit"]
    entry["updated_on"] = today()
    save_manifest(manifest)
    # An approved update is not a custom modification: move this skill's baseline forward.
    take_snapshot([args.name])
    log_event(args.name, "updated", summary=args.summary or "updated from upstream",
              from_ref=old_commit[:7], to_ref=res["latest_commit"][:7], rationale=args.rationale)
    print(json.dumps({"installed": args.name, "commit": res["latest_commit"], "target": str(target)}, indent=2))
