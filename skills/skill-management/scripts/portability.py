"""Export/sync to the configured folder, log import, and the HTML dashboard."""
import datetime as dt
import html
import io
import json
import re
import shutil
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

import core
import health
import insights
from core import BACKUPS, DISABLED, SKILLS, frontmatter


def _log_markdown():
    buf = io.StringIO()
    with redirect_stdout(buf):
        core.cmd_log(type("A", (), {"log_cmd": "show"})())
    return buf.getvalue()


NOTE_START = "<!-- skill-management:log:start -->"
NOTE_END = "<!-- skill-management:log:end -->"
DASH_START = "<!-- skill-management:dashboard:start -->"
DASH_END = "<!-- skill-management:dashboard:end -->"
# Matches the user's revision property however it is spelled: last-revision, Last revision, last_revision.
REVISION_PROP = re.compile(r"(?mi)^(last[ _-]?revision)[ \t]*:.*$")


def _replace_block(body, start, end, block):
    before, rest = body.split(start, 1)
    return before + block + rest.split(end, 1)[1]


def _dashboard_links(note):
    """Refresh the dashboard file and return the Markdown links to it (vault link, plus online link if published)."""
    cfg = core.load_config()
    export_dir = Path(cfg.get("export_dir") or "")
    target = export_dir / "Skills dashboard.html" if str(export_dir) and export_dir.is_dir() else BACKUPS / "dashboard.html"
    target.write_text(render(collect()), encoding="utf-8")

    vault = next((p for p in note.parents if (p / ".obsidian").is_dir()), None)
    if vault and vault in target.parents:
        links = [f"[[{target.relative_to(vault).as_posix()}|Open the skills dashboard]]"]
    else:
        links = [f"[Open the skills dashboard]({target.as_uri()})"]
    if cfg.get("dashboard_artifact_url"):
        links.append(f"[online version]({cfg['dashboard_artifact_url']})")
    return links, str(target)


def update_obsidian_note(path=None):
    """Write the skills log into the configured Obsidian note, with a dashboard link at the top,
    and set its revision property to the current date and time.

    Only the blocks between the markers are replaced; other note content and properties are kept.
    On first use (no log markers) the note body after the frontmatter is replaced by the managed blocks.
    """
    note = Path(path or core.load_config().get("obsidian_note") or "")
    if not str(note) or not note.parent.is_dir():
        return {"error": f"Obsidian note folder not reachable: {note}"}
    text = note.read_text(encoding="utf-8") if note.exists() else ""
    # Obsidian's date & time property format.
    revised = dt.datetime.now().strftime("%Y-%m-%dT%H:%M")

    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    fm, body = (fm_match.group(1), text[fm_match.end():]) if fm_match else ("", text)
    if REVISION_PROP.search(fm):
        fm = REVISION_PROP.sub(lambda m: f"{m.group(1)}: {revised}", fm, count=1)
    else:
        fm = (fm + "\n" if fm else "") + f"last-revision: {revised}"

    links, dashboard = _dashboard_links(note)
    dash_block = f"{DASH_START}\n📊 {' · '.join(links)} (updated {revised.replace('T', ' ')})\n{DASH_END}"
    log_block = f"{NOTE_START}\n{_log_markdown().strip()}\n{NOTE_END}"
    if NOTE_START in body and NOTE_END in body:
        body = _replace_block(body, NOTE_START, NOTE_END, log_block)
        mode = "replaced managed block"
    else:
        body = f"# Log\n\n{log_block}\n"
        mode = "first write: body replaced with managed block"
    if DASH_START in body and DASH_END in body:
        body = _replace_block(body, DASH_START, DASH_END, dash_block)
    else:
        body = f"{dash_block}\n\n{body.lstrip()}"
    note.write_text(f"---\n{fm}\n---\n{body}", encoding="utf-8")
    return {"note": str(note), "last_revision": revised, "dashboard": dashboard, "mode": mode}


def cmd_obsidian_note(args):
    print(json.dumps(update_obsidian_note(args.path), indent=2, ensure_ascii=False))


def cmd_notes_status(_args):
    """List skills missing from or stale in the skills notes folder, and each note's revision date."""
    folder = Path(core.load_config().get("notes_folder") or "")
    if not str(folder) or not folder.is_dir():
        print(json.dumps({"error": f"notes_folder not reachable: {folder}"}, indent=2))
        return
    rows, _synced = core.log_rows()
    explained = folder / "00_Explained_placeholder"
    for f in folder.glob("*.md"):
        if "explained" in f.name.lower():
            explained = f
    text = explained.read_text(encoding="utf-8").lower() if explained.is_file() else ""

    def mentioned(name):
        return re.search(r"(?<![\w-])" + re.escape(name.lower()) + r"(?![\w-])", text) is not None

    missing, stale = [], []
    live = {r["name"] for r in rows if r["kind"] in ("local", "claude.ai") and not r["removed"]}
    for r in rows:
        if r["kind"] not in ("local", "claude.ai"):
            continue
        name = r["name"]
        if r["removed"]:
            if mentioned(name) and name not in live:
                stale.append(name)
        elif not mentioned(name):
            missing.append(name)
    notes = []
    for f in sorted(folder.glob("*.md")):
        m = REVISION_PROP.search(f.read_text(encoding="utf-8"))
        notes.append({"note": f.name, "revision": m.group(0) if m else None,
                      "modified": dt.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")})
    print(json.dumps({"folder": str(folder), "explained_note": explained.name,
                      "installed_but_not_in_explained": missing,
                      "in_explained_but_removed": stale, "notes": notes}, indent=2, ensure_ascii=False))


def _usage():
    stats = {}
    for ts, _session, tool, inp in core.transcript_events():
        name = insights._skill_hit(tool, inp)
        if name:
            s = stats.setdefault(name, {"uses": 0, "last_used": ""})
            s["uses"] += 1
            s["last_used"] = max(s["last_used"], ts[:10])
    return stats


def _last_check():
    runs = sorted(core.RUNS.glob("*/summary.json")) if core.RUNS.is_dir() else []
    return json.loads(runs[-1].read_text(encoding="utf-8")) if runs else None


def collect():
    rows, synced_on = core.log_rows()
    usage = _usage()
    check = _last_check()
    updates = {r["name"]: r["status"] for r in (check or {}).get("results", [])}
    tracked = {e["name"] for e in core.load_manifest()["skills"]}
    out = []
    for r in rows:
        s, kind = r["log"], r["kind"]
        path = Path(r["path"]) if r.get("path") else None
        if path and (path / "SKILL.md").is_file():
            skill_dirs = [path]
        elif path and (path / "skills").is_dir():
            skill_dirs = [d for d in (path / "skills").iterdir() if (d / "SKILL.md").is_file()]
        else:
            skill_dirs = []
        costs = [health.skill_cost(d) for d in skill_dirs]
        issues = health.validate_skill(path) if kind == "local" and path and not r["removed"] else []
        names = r.get("skills") or [r["name"]]
        uses = sum(usage.get(n, {}).get("uses", 0) for n in names)
        last = max([usage.get(n, {}).get("last_used", "") for n in names] or [""])
        if kind == "local":
            update = updates.get(r["name"], "not checked" if r["name"] in tracked else "not tracked")
        else:
            update = "managed by Claude app"
        out.append({**r, "purpose": s.get("purpose", ""), "source": s.get("source", ""),
                    "installed": s.get("installed") or "unknown", "uses": uses, "last_used": last,
                    "cost": {"always_on_tokens": sum(c["always_on_tokens"] for c in costs),
                             "on_use_tokens": sum(c["on_use_tokens"] for c in costs)} if costs else None,
                    "errors": [i["issue"] for i in issues if i["level"] == "error"],
                    "warnings": [i["issue"] for i in issues if i["level"] == "warn"],
                    "update": update, "packaged": s.get("packaged"),
                    "skill_count": len(r.get("skills") or [1])})
    events = []
    for r in rows:
        s, label = r["log"], r["name"]
        if s.get("installed"):
            events.append((s["installed"], label, "Installed", s.get("source", "")))
        why = lambda e: f" — why: {e['rationale']}" if e.get("rationale") else ""
        events += [(m["date"], label, f"Modified by {m['by']}", m["summary"] + why(m)) for m in s.get("modifications", [])]
        events += [(u["date"], label, "Updated", u["summary"] + why(u)) for u in s.get("updates", [])]
        if s.get("packaged"):
            events.append((s["packaged"]["date"], label, "Packaged for claude.ai", s["packaged"]["file"]))
        if s.get("disabled"):
            events.append((s["disabled"]["date"], label, "Disabled", s["disabled"]["reason"]))
        if s.get("uninstalled"):
            events.append((s["uninstalled"]["date"], label, "Uninstalled", s["uninstalled"]["reason"]))
    run_dir = (check or {}).get("run_dir", "")
    return {"rows": out, "events": sorted(events, reverse=True), "synced_on": synced_on,
            "checked": Path(run_dir).name if run_dir else None}


CSS = """
:root{--bg:#F4F6F5;--surface:#FFFFFF;--ink:#1B2220;--muted:#5B6863;--line:#D9DFDC;--accent:#0E6B5F;
--accent-soft:#E1F0EC;--ok:#2F7A4D;--ok-soft:#E3F2E8;--warn:#9A6212;--warn-soft:#FBF0DC;--crit:#B42318;--crit-soft:#FBE7E5;
--sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--cond:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,sans-serif;
--mono:"IBM Plex Mono",ui-monospace,"Cascadia Mono",Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111615;--surface:#19201E;--ink:#E4EBE8;
--muted:#97A5A0;--line:#2B3532;--accent:#5CC2AF;--accent-soft:#16332D;--ok:#6CC08C;--ok-soft:#15301F;--warn:#E3B062;
--warn-soft:#342812;--crit:#F08A80;--crit-soft:#3A1916}}
:root[data-theme="dark"]{--bg:#111615;--surface:#19201E;--ink:#E4EBE8;--muted:#97A5A0;--line:#2B3532;--accent:#5CC2AF;
--accent-soft:#16332D;--ok:#6CC08C;--ok-soft:#15301F;--warn:#E3B062;--warn-soft:#342812;--crit:#F08A80;--crit-soft:#3A1916}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 var(--sans)}
.wrap{max-width:1180px;margin:0 auto;padding-inline:20px;padding-block:32px 56px;display:grid;gap:36px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 24px;border-bottom:1px solid var(--line);padding-bottom:18px}
h1,h2{font-family:var(--cond);font-weight:600;letter-spacing:-.01em;text-wrap:balance;margin:0}
h1{font-size:2rem}h2{font-size:1.25rem;margin-bottom:12px}
.meta{color:var(--muted);font:13px var(--mono)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:6px;overflow:hidden}
.stat{background:var(--surface);padding:14px 16px}
.stat b{display:block;font:600 1.6rem/1.1 var(--mono);font-variant-numeric:tabular-nums}
.stat span{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}
.attention{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.attention li{display:flex;gap:12px;align-items:flex-start;padding:10px 12px;background:var(--surface);border:1px solid var(--line);border-radius:6px}
.attention .none{color:var(--muted)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:var(--surface)}
table{border-collapse:collapse;width:100%;min-width:820px}
th,td{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line)}
th{font:600 11px var(--sans);text-transform:uppercase;letter-spacing:.07em;color:var(--muted);background:var(--bg)}
tr:last-child td{border-bottom:0}
td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
.name{font:600 14px var(--mono)}
.small{color:var(--muted);font-size:13px}
.pill{display:inline-block;font:600 11px var(--sans);letter-spacing:.04em;text-transform:uppercase;padding:2px 8px;border-radius:999px;white-space:nowrap}
.p-ok{background:var(--ok-soft);color:var(--ok)}.p-warn{background:var(--warn-soft);color:var(--warn)}
.p-crit{background:var(--crit-soft);color:var(--crit)}.p-muted{background:var(--bg);color:var(--muted);border:1px solid var(--line)}
.p-accent{background:var(--accent-soft);color:var(--accent)}
.timeline{list-style:none;margin:0;padding:0;border-left:2px solid var(--line);display:grid;gap:14px}
.timeline li{padding-left:16px;position:relative}
.timeline li::before{content:"";position:absolute;left:-6px;top:7px;width:10px;height:10px;border-radius:50%;background:var(--accent)}
.timeline .when{font:13px var(--mono);color:var(--muted)}
tr.group th{background:var(--accent-soft);color:var(--ink);font:600 13px var(--cond);text-transform:none;letter-spacing:0;padding:8px 12px}
tr.group th span{font:400 12px var(--sans);color:var(--muted);margin-left:8px}
@media (max-width:560px){h1{font-size:1.6rem}.wrap{padding-inline:16px}}
"""


def _pill(text, kind):
    return f'<span class="pill p-{kind}">{html.escape(text)}</span>'


def _avail_pill(text):
    kind = "ok" if text.startswith("✅") else "warn" if text.startswith("⏸") else "muted"
    return _pill(text.lstrip("✅⏸—✗ ").strip(), kind)


GROUPS = [("local", "Your skills on this computer", "Claude Code only, unless uploaded to claude.ai"),
          ("claude.ai", "claude.ai account skills", "yours and Anthropic's, synced into Claude Code"),
          ("plugin", "Claude app plugins", "skills grouped by plugin"),
          ("cli plugin", "Claude Code CLI plugins", "installed with the claude CLI"),
          ("removed", "Removed", "kept for history")]


def render(data):
    rows, e = data["rows"], html.escape
    live = [r for r in rows if not r["removed"]]
    in_chat = sum(r["skill_count"] for r in live if r["chat"].startswith("✅"))
    in_code = sum(r["skill_count"] for r in live if r["code"].startswith("✅"))
    always_on = sum(r["cost"]["always_on_tokens"] for r in live if r["cost"] and r["code"].startswith("✅"))
    attention = []
    for r in rows:
        name = e(r["name"])
        for issue in r["errors"]:
            attention.append((0, _pill("error", "crit"), f"<b>{name}</b>: {e(issue)}"))
        for issue in r["warnings"]:
            attention.append((1, _pill("warning", "warn"), f"<b>{name}</b>: {e(issue)}"))
        if r["update"] == "update_available":
            attention.append((1, _pill("update", "accent"),
                              f"<b>{name}</b>: a newer version is available. Run a skills check to review it."))
        if r["duplicate"]:
            attention.append((1, _pill("duplicate", "warn"),
                              f"<b>{name}</b>: active locally and on claude.ai, so Claude Code loads it twice. Disable the local copy."))
        if r["packaged"] and r["chat"].startswith("—"):
            attention.append((2, _pill("to upload", "accent"),
                              f"<b>{name}</b>: claude.ai package ready since {e(r['packaged']['date'])}, not uploaded yet."))
    if data["synced_on"] and (dt.date.today() - dt.date.fromisoformat(data["synced_on"])).days > 7:
        attention.append((1, _pill("stale", "warn"),
                          f"The claude.ai skill list is from {e(data['synced_on'])}. Open the Claude app to refresh it."))
    attention.sort(key=lambda a: a[0])

    update_kind = {"up_to_date": "ok", "update_available": "accent", "error": "crit"}
    body_rows = []
    for key, title, sub in GROUPS:
        if key == "removed":
            members = [r for r in rows if r["removed"]]
        elif key == "claude.ai":
            members = [r for r in live if r["kind"] in ("claude.ai", "app built-in")]
        else:
            members = [r for r in live if r["kind"] == key]
        if not members:
            continue
        body_rows.append(f"<tr class='group'><th colspan='8'>{e(title)} <span>{len(members)} · {e(sub)}</span></th></tr>")
        for r in members:
            if r["errors"]:
                health_cell = _pill(f"{len(r['errors'])} error", "crit")
            elif r["warnings"]:
                health_cell = _pill(f"{len(r['warnings'])} warning", "warn")
            elif r["kind"] == "local" and not r["removed"]:
                health_cell = _pill("healthy", "ok")
            else:
                health_cell = "—"
            cost = f"{r['cost']['always_on_tokens']:,} / {r['cost']['on_use_tokens']:,}" if r["cost"] else "—"
            body_rows.append(
                f"<tr><td><div class='name'>{e(r['name'])}</div><div class='small'>{e(r['purpose'] or '')}</div></td>"
                f"<td>{_avail_pill(r['chat'])}</td><td>{_avail_pill(r['code'])}</td><td>{health_cell}</td>"
                f"<td>{_pill(r['update'].replace('_', ' '), update_kind.get(r['update'], 'muted'))}</td>"
                f"<td class='num'>{r['uses']}<div class='small'>{e(r['last_used'] or 'never recorded')}</div></td>"
                f"<td class='num'>{cost}</td><td class='small'>{e(r['source'])}<br>installed {e(r['installed'])}</td></tr>")
    events = "".join(
        f"<li><div class='when'>{e(d)} · {e(n)}</div><div><b>{e(kind)}</b>{': ' + e(text) if text else ''}</div></li>"
        for d, n, kind, text in data["events"][:60]) or "<li>No events yet.</li>"
    attention_html = "".join(f"<li>{p}<div>{t}</div></li>" for _, p, t in attention) or \
        "<li class='none'>Nothing needs attention.</li>"
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<meta charset="utf-8">
<title>Skill Management</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header><h1>Skill Management</h1><div class="meta">generated {generated} · last update check {e(data['checked'] or 'never')} · claude.ai list as of {e(data['synced_on'] or 'unknown')}</div></header>
<section class="stats" aria-label="Summary">
<div class="stat"><b>{in_chat}</b><span>skills in Claude chat</span></div>
<div class="stat"><b>{in_code}</b><span>skills in Claude Code</span></div>
<div class="stat"><b>{sum(1 for r in live if r['kind'] == 'local')}</b><span>local skills</span></div>
<div class="stat"><b>{sum(1 for a in attention if a[0] == 0)}</b><span>health errors</span></div>
<div class="stat"><b>{sum(r['update'] == 'update_available' for r in rows)}</b><span>updates waiting</span></div>
<div class="stat"><b>~{always_on:,}</b><span>tokens every Code session</span></div>
</section>
<section><h2>Needs attention</h2><ul class="attention">{attention_html}</ul></section>
<section><h2>Skills</h2><div class="scroll"><table>
<thead><tr><th>Skill</th><th>Claude chat</th><th>Claude Code</th><th>Health</th><th>Updates</th><th>Uses</th><th>Tokens always / on use</th><th>Source</th></tr></thead>
<tbody>{''.join(body_rows)}</tbody></table></div></section>
<section><h2>History</h2><ul class="timeline">{events}</ul></section>
</div>
"""


def cmd_dashboard(args):
    page = render(collect())
    out = Path(args.out) if args.out else BACKUPS / "dashboard.html"
    out.write_text(page, encoding="utf-8")
    print(json.dumps({"dashboard": str(out)}, indent=2))


def cmd_export(args):
    cfg = core.load_config()
    dest = Path(args.dest or cfg.get("export_dir") or "")
    if not str(dest) or not dest.parent.exists():
        raise SystemExit(json.dumps({"error": f"export folder not reachable: {dest}"}))
    (dest / "exports").mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    zpath = dest / "exports" / f"skills-export-{stamp}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in SKILLS.rglob("*"):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, f.relative_to(SKILLS.parent))
        if DISABLED.is_dir():
            for f in DISABLED.rglob("*"):
                if f.is_file():
                    z.write(f, Path("disabled") / f.relative_to(DISABLED))
        if core.LOG.exists():
            z.write(core.LOG, "skills-log.json")
    keep = cfg.get("keep_exports", 8)
    exports = sorted((dest / "exports").glob("skills-export-*.zip"))
    for old in exports[:-keep]:
        old.unlink()

    today = core.today()
    note = (f"---\nupdated: {today}\ntags: [claude, skills]\n---\n\n# Skills log\n\n"
            f"Exported {dt.datetime.now():%Y-%m-%d %H:%M} from `{SKILLS}`. "
            f"Dashboard: [[Skills dashboard.html]]. Latest export: `exports/{zpath.name}`.\n\n{_log_markdown()}\n")
    (dest / "Skills log.md").write_text(note, encoding="utf-8")
    (dest / "Skills dashboard.html").write_text(render(collect()), encoding="utf-8")
    written = ["Skills log.md", "Skills dashboard.html", f"exports/{zpath.name}"]
    if args.report and Path(args.report).is_file():
        (dest / "Reports").mkdir(exist_ok=True)
        name = f"Reports/{today} skills report.md"
        shutil.copy2(args.report, dest / name)
        written.append(name)
    note = update_obsidian_note() if core.load_config().get("obsidian_note") else None
    print(json.dumps({"export_dir": str(dest), "written": written, "obsidian_note": note}, indent=2, ensure_ascii=False))


def cmd_import_log(args):
    """Merge the skills log from an export zip into the local log (events are de-duplicated)."""
    with zipfile.ZipFile(args.zip) as z:
        incoming = json.loads(z.read("skills-log.json").decode("utf-8"))["skills"]
    log = core.load_log()
    for name, s in incoming.items():
        mine = log["skills"].setdefault(name, s)
        if mine is s:
            continue
        for key in ("modifications", "updates"):
            seen = {json.dumps(x, sort_keys=True) for x in mine[key]}
            mine[key] += [x for x in s[key] if json.dumps(x, sort_keys=True) not in seen]
            mine[key].sort(key=lambda x: x["date"])
        for key in ("purpose", "source", "installed"):
            mine[key] = mine.get(key) or s.get(key)
    core.save_log(log)
    print(json.dumps({"merged_skills": sorted(incoming)}, indent=2))
