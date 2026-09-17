"""Lifecycle commands: install (stage + place), disable/enable/uninstall, backups/restore, new skill."""
import datetime as dt
import difflib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import core
from core import DISABLED, RUNS, SKILLS, frontmatter, git, log_event, make_backup, today

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
GITHUB_TREE = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/([^/]+)(?:/(.*))?)?/?$")


def _stamp():
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _fail(msg):
    sys.exit(json.dumps({"error": msg}))


def _find_skill_dirs(root):
    return sorted({p.parent for p in root.rglob("SKILL.md") if ".git" not in p.parts})


# ---------- install ----------

def cmd_stage_install(args):
    """Fetch a skill into a staging folder. Nothing is installed."""
    stage_root = RUNS / _stamp() / "install"
    meta = {"source": args.source}
    src = args.source
    subdir = args.subdir
    with tempfile.TemporaryDirectory() as tmp:
        m = GITHUB_TREE.match(src)
        if m or src.endswith(".git") or src.startswith("git@"):
            repo = f"https://github.com/{m.group(1)}/{m.group(2)}" if m else src
            branch = args.ref or (m.group(3) if m else None)
            subdir = subdir or (m.group(4) if m else None)
            clone = Path(tmp) / "repo"
            cmd = ["clone", "--quiet", "--depth", "1"] + (["--branch", branch] if branch else []) + [repo, str(clone)]
            git(*cmd)
            meta.update(repo=repo, branch=branch or git("rev-parse", "--abbrev-ref", "HEAD", cwd=clone).stdout.strip(),
                        commit=git("rev-parse", "HEAD", cwd=clone).stdout.strip())
            base = clone
        elif Path(src).is_file() and src.lower().endswith(".zip"):
            base = Path(tmp) / "zip"
            with zipfile.ZipFile(src) as z:
                z.extractall(base)
        elif Path(src).is_dir():
            base = Path(src)
        else:
            _fail(f"unsupported source: {src}")

        candidates = _find_skill_dirs(base / subdir if subdir else base)
        rel = [c.relative_to(base).as_posix() for c in candidates]
        if not candidates:
            _fail("no SKILL.md found in source")
        if len(candidates) > 1 and not subdir:
            print(json.dumps({"status": "choose_one", "skills_found": rel,
                              "hint": "re-run with --subdir <one of skills_found>"}, indent=2))
            return
        skill_dir = candidates[0] if len(candidates) == 1 else base / subdir
        fm = frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8")) or {}
        name = args.name or fm.get("name") or skill_dir.name
        stage_root.mkdir(parents=True, exist_ok=True)
        staged = stage_root / name
        shutil.copytree(skill_dir, staged, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        upstream_prefix = skill_dir.relative_to(base).as_posix()
        meta.update(
            name=name,
            subdir=upstream_prefix,
            staged_dir=str(staged),
            files={f.relative_to(staged).as_posix():
                   (f"{upstream_prefix}/" if upstream_prefix != "." else "") + f.relative_to(staged).as_posix()
                   for f in staged.rglob("*") if f.is_file()},
            local_patches=[],
            already_installed=(SKILLS / name).exists(),
            description=fm.get("description", ""),
        )
    (stage_root / f"{name}.stage.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({**meta, "stage_file": str(stage_root / f"{name}.stage.json")}, indent=2, ensure_ascii=False))


def cmd_place(args):
    """Install a staged skill (after scan + approval). Tracks GitHub sources in the manifest."""
    meta = json.loads(Path(args.stage_file).read_text(encoding="utf-8"))
    name, staged = meta["name"], Path(meta["staged_dir"])
    target = SKILLS / name
    if not NAME_RE.match(name):
        _fail(f"invalid skill name '{name}' (lowercase letters, digits, hyphens; max 64)")
    if target.exists() and not args.replace:
        _fail(f"{name} is already installed; pass --replace to overwrite (a backup is taken first)")
    backup = make_backup()
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(staged, target)

    if meta.get("repo"):
        manifest = core.load_manifest()
        manifest["skills"] = [e for e in manifest["skills"] if e["name"] != name]
        manifest["skills"].append({
            "name": name, "repo": meta["repo"], "branch": meta["branch"], "installed_commit": meta["commit"],
            "installed_on": today(), "files": meta["files"], "local_patches": meta.get("local_patches", []),
        })
        core.save_manifest(manifest)
    core.take_snapshot([name])
    source = f"GitHub {meta['repo'].split('github.com/')[-1]}@{meta['commit'][:7]}" if meta.get("repo") else meta["source"]
    log_event(name, "installed", source=source, purpose=args.purpose)
    print(json.dumps({"installed": name, "target": str(target), "backup": backup["backup"],
                      "tracked": bool(meta.get("repo"))}, indent=2))


# ---------- disable / enable / uninstall ----------

def cmd_disable(args):
    src, dst = SKILLS / args.name, DISABLED / args.name
    if not src.is_dir():
        _fail(f"{args.name} is not an active user skill")
    if dst.exists():
        _fail(f"a disabled copy of {args.name} already exists at {dst}")
    DISABLED.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    core.take_snapshot([args.name])
    log_event(args.name, "disabled", reason=args.reason)
    print(json.dumps({"disabled": args.name, "moved_to": str(dst)}, indent=2))


def cmd_enable(args):
    src, dst = DISABLED / args.name, SKILLS / args.name
    if not src.is_dir():
        _fail(f"{args.name} is not disabled")
    if dst.exists():
        _fail(f"{args.name} already exists in the skills folder")
    shutil.move(str(src), str(dst))
    core.take_snapshot([args.name])
    log_event(args.name, "enabled")
    print(json.dumps({"enabled": args.name}, indent=2))


def cmd_uninstall(args):
    folder = SKILLS / args.name if (SKILLS / args.name).is_dir() else DISABLED / args.name
    if not folder.is_dir():
        _fail(f"{args.name} is not installed or disabled")
    if args.name == core.SELF:
        _fail("refusing to uninstall skill-management itself")
    backup = make_backup()
    keep = core.BACKUPS / "uninstalled"
    keep.mkdir(parents=True, exist_ok=True)
    archive = shutil.make_archive(str(keep / f"{args.name}-{_stamp()}"), "zip", folder.parent, folder.name)
    shutil.rmtree(folder)
    manifest = core.load_manifest()
    manifest["skills"] = [e for e in manifest["skills"] if e["name"] != args.name]
    core.save_manifest(manifest)
    core.take_snapshot([args.name])
    log_event(args.name, "uninstalled", reason=args.reason)
    print(json.dumps({"uninstalled": args.name, "archived_copy": archive, "backup": backup["backup"]}, indent=2))


# ---------- backups / restore ----------

def _zip_skills(path):
    with zipfile.ZipFile(path) as z:
        names = {n.split("/")[1] for n in z.namelist() if n.startswith("skills/") and n.count("/") >= 2}
    return sorted(names)


def cmd_backups(_args):
    rows = []
    export_dir = core.load_config().get("export_dir")
    folders = [core.BACKUPS, core.BACKUPS / "uninstalled"] + ([Path(export_dir) / "exports"] if export_dir else [])
    for folder in folders:
        if not folder.is_dir():
            continue
        for z in sorted(folder.glob("*.zip"), reverse=True):
            try:
                skills = _zip_skills(z)
            except zipfile.BadZipFile:
                continue
            rows.append({"file": str(z), "taken": dt.datetime.fromtimestamp(z.stat().st_mtime).isoformat(timespec="minutes"),
                         "skills": skills or "(single-skill archive)"})
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def cmd_restore(args):
    zpath = Path(args.backup)
    out = RUNS / _stamp() / "restore"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(out / "extracted")
    root = out / "extracted" / "skills"
    if not root.is_dir():  # single-skill archive from uninstall: <name>/...
        root = out / "extracted"
    available = sorted(d.name for d in root.iterdir() if (d / "SKILL.md").is_file())
    names = args.name or available
    missing = [n for n in names if n not in available]
    if missing:
        _fail(f"not in this backup: {missing}; available: {available}")

    preview = []
    for n in names:
        before, after = SKILLS / n, root / n
        current = {f.relative_to(before).as_posix() for f in before.rglob("*") if f.is_file()} if before.is_dir() else set()
        files = sorted(current | {f.relative_to(after).as_posix() for f in after.rglob("*") if f.is_file()})
        diff = []
        for rel in files:
            diff += difflib.unified_diff(core.read_text(before / rel), core.read_text(after / rel),
                                         f"current/{n}/{rel}", f"backup/{n}/{rel}")
        (out / f"{n}.diff").write_text("".join(diff), encoding="utf-8")
        preview.append({"name": n, "currently_installed": before.is_dir(), "diff_file": str(out / f"{n}.diff"),
                        "diff_lines": len(diff), "identical": not diff})
    if args.preview:
        print(json.dumps({"preview": preview, "backup": str(zpath)}, indent=2))
        return

    safety = make_backup(label="skills-before-restore")
    taken = dt.datetime.fromtimestamp(zpath.stat().st_mtime).date().isoformat()
    for n in names:
        if (SKILLS / n).exists():
            shutil.rmtree(SKILLS / n)
        shutil.copytree(root / n, SKILLS / n)
        log_event(n, "restored", summary=f"Rolled back to the backup of {taken}" + (f": {args.reason}" if args.reason else ""))
    core.take_snapshot(names)
    print(json.dumps({"restored": names, "from": str(zpath), "safety_backup": safety["backup"]}, indent=2))


# ---------- create ----------

TEMPLATE = """---
name: {name}
description: "{description}"
---

# {title}

## When to use
- ...

## Steps
1. ...

## Output
- ...
"""


def cmd_new(args):
    if not NAME_RE.match(args.name):
        _fail("name must be lowercase letters, digits and hyphens (max 64)")
    target = SKILLS / args.name
    if target.exists():
        _fail(f"{args.name} already exists")
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(TEMPLATE.format(
        name=args.name, description=args.description.replace('"', "'"),
        title=args.name.replace("-", " ").capitalize()), encoding="utf-8")
    core.take_snapshot([args.name])
    log_event(args.name, "installed", source="own (created with skill-management)", purpose=args.purpose)
    print(json.dumps({"created": str(target / "SKILL.md")}, indent=2))
