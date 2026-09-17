"""Usage statistics and per-invocation session context (request, output, user reaction)."""
import datetime as dt
import json
from pathlib import Path

import core

SKIP_PREFIXES = ("<system-reminder>", "Tool loaded", "Base directory for this skill", "Caveat:", "<local-command")
ANSWER_MARKERS = ("The user answered", "Your questions have been answered", "doesn't want to proceed",
                  "The user rejected", "user denied", "was rejected")


def _skill_hit(tool, inp):
    if tool == "Skill":
        return str(inp.get("skill", "")).split(":")[-1]
    if tool == "Read":
        p = str(inp.get("file_path", "")).replace("\\", "/")
        if p.endswith("/SKILL.md") and "/.claude/skills/" in p:
            return Path(p).parent.name
    return None


def cmd_usage(args):
    since = dt.datetime.fromisoformat(args.since).replace(tzinfo=dt.timezone.utc) if args.since else None
    stats = {}
    for ts, session, tool, inp in core.transcript_events(since):
        name = _skill_hit(tool, inp)
        if not name:
            continue
        s = stats.setdefault(name, {"uses": 0, "sessions": set(), "first_used": ts[:10], "last_used": ""})
        s["uses"] += 1
        s["sessions"].add(session)
        s["first_used"] = min(s["first_used"], ts[:10])
        s["last_used"] = max(s["last_used"], ts[:10])
    out = {k: {**v, "sessions": len(v["sessions"])} for k, v in sorted(stats.items())}
    installed = core.user_skills()
    cutoff = (dt.date.today() - dt.timedelta(days=args.unused_days)).isoformat()
    unused = []
    for n in installed:
        installed_on = core.load_log()["skills"].get(n, {}).get("installed") or "0000"
        if installed_on <= cutoff and out.get(n, {}).get("last_used", "") < cutoff:
            unused.append(n)
    print(json.dumps({"since": args.since or "all sessions", "usage": out,
                      f"user_skills_unused_{args.unused_days}d": unused,
                      "note": "counts explicit invocations and SKILL.md reads; plugin skills appear by short name"},
                     indent=2, ensure_ascii=False))


def _entries(jf):
    """Ordered, simplified conversation entries from one transcript."""
    rows = []
    with open(jf, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind, msg, ts = d.get("type"), d.get("message") or {}, d.get("timestamp", "")
            content = msg.get("content")
            items = [{"type": "text", "text": content}] if isinstance(content, str) else content or []
            for it in items:
                if not isinstance(it, dict):
                    continue
                t = it.get("type")
                if kind == "user" and t == "text" and not d.get("isMeta"):
                    text = it.get("text", "").strip()
                    if text and not text.startswith(SKIP_PREFIXES):
                        rows.append(("user", ts, text))
                elif kind == "user" and t == "tool_result":
                    c = it.get("content")
                    text = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
                    if any(m in text for m in ANSWER_MARKERS):
                        rows.append(("user", ts, text.strip()))
                elif kind == "assistant" and t == "text" and it.get("text", "").strip():
                    rows.append(("assistant", ts, it["text"].strip()))
                elif kind == "assistant" and t == "tool_use":
                    name = _skill_hit(it.get("name"), it.get("input") or {})
                    if name:
                        rows.append(("skill", ts, name))
    return rows


def cmd_sessions(args):
    cut = lambda s, n: s if len(s) <= n else s[:n] + " …"
    found = []
    for jf in core.TRANSCRIPTS.glob("*/*.jsonl"):
        if "trigger-tests" in jf.parent.name:
            continue
        rows = _entries(jf)
        for i, (kind, ts, val) in enumerate(rows):
            if kind != "skill" or val != args.skill:
                continue
            request = next((r[2] for r in reversed(rows[:i]) if r[0] == "user"), "")
            after = rows[i + 1:]
            nxt = next((j for j, r in enumerate(after) if r[0] == "user"), len(after))
            outputs = [r[2] for r in after[:nxt] if r[0] == "assistant"]
            reactions = [r[2] for r in after[nxt:] if r[0] == "user"][:args.reactions]
            found.append({
                "date": ts[:10], "session": jf.stem,
                "request": cut(request, 500),
                "final_output": cut(outputs[-1], 1200) if outputs else "",
                "user_reactions": [cut(r, 600) for r in reactions],
                "interrupted": any("[Request interrupted" in r for r in reactions),
            })
    found.sort(key=lambda r: r["date"], reverse=True)
    print(json.dumps({"skill": args.skill, "invocations_found": len(found), "items": found[:args.limit]},
                     indent=2, ensure_ascii=False))
