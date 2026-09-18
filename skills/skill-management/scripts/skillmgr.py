#!/usr/bin/env python3
"""skill-management CLI. Run `python skillmgr.py -h` or `<command> -h` for details.

Inventory & history : inventory, usage, sessions, log show|event, changes, snapshot
Updates             : backup, check, apply
Lifecycle           : stage-install, place, disable, enable, uninstall, backups, restore, new
Health              : validate, cost, trigger-test
claude.ai & plugins : where, sync-remote, pull-claude-ai, package
Portability         : export, import-log, obsidian-note, dashboard, publish-repo
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill folder
sys.path.insert(0, str(Path(__file__).resolve().parent))

import core  # noqa: E402
import health  # noqa: E402
import insights  # noqa: E402
import lifecycle  # noqa: E402
import portability  # noqa: E402
import publish  # noqa: E402
import remote  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def cmd(name, fn, help_text):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(fn=fn)
        return p

    # inventory & history
    p = cmd("inventory", core.cmd_inventory, "user, project and disabled skills")
    p.add_argument("--full", action="store_true", help="full descriptions")
    p = cmd("usage", insights.cmd_usage, "how often each skill was used")
    p.add_argument("--since", help="YYYY-MM-DD")
    p.add_argument("--unused-days", type=int, default=30)
    p = cmd("sessions", insights.cmd_sessions, "requests, outputs and your reactions for a skill's uses")
    p.add_argument("--skill", required=True)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--reactions", type=int, default=2)
    cmd("changes", core.cmd_changes, "edits, installs and removals since the last baseline")
    p = cmd("snapshot", core.cmd_snapshot, "save the current state as the new baseline")
    p.add_argument("--name", nargs="*", help="only these skills")
    lg = cmd("log", core.cmd_log, "skills history log")
    lsub = lg.add_subparsers(dest="log_cmd", required=True)
    lsub.add_parser("show")
    ev = lsub.add_parser("event")
    ev.add_argument("--skill", required=True)
    ev.add_argument("--type", required=True,
                    choices=["installed", "modified", "updated", "uninstalled", "disabled", "enabled", "restored", "purpose", "rationale"])
    for flag in ("--date", "--by", "--summary", "--source", "--purpose", "--reason", "--rationale"):
        ev.add_argument(flag)
    ev.add_argument("--from", dest="from_ref")
    ev.add_argument("--to", dest="to_ref")

    # updates
    p = cmd("backup", core.cmd_backup, "zip all user skills")
    p.add_argument("--keep", type=int)
    cmd("check", core.cmd_check, "check tracked skills for upstream updates (stages only)")
    p = cmd("apply", core.cmd_apply, "install a staged update")
    p.add_argument("--run", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--summary")
    p.add_argument("--rationale", help="the user's reason for the update")

    # lifecycle
    p = cmd("stage-install", lifecycle.cmd_stage_install, "fetch a skill from GitHub, a folder or a zip into staging")
    p.add_argument("--source", required=True)
    p.add_argument("--subdir")
    p.add_argument("--name")
    p.add_argument("--ref", help="branch or tag")
    p = cmd("place", lifecycle.cmd_place, "install a staged skill")
    p.add_argument("--stage-file", required=True)
    p.add_argument("--purpose")
    p.add_argument("--replace", action="store_true")
    p = cmd("disable", lifecycle.cmd_disable, "move a skill out of Claude's reach (reversible)")
    p.add_argument("--name", required=True)
    p.add_argument("--reason")
    p = cmd("enable", lifecycle.cmd_enable, "bring a disabled skill back")
    p.add_argument("--name", required=True)
    p = cmd("uninstall", lifecycle.cmd_uninstall, "remove a skill (archived copy kept)")
    p.add_argument("--name", required=True)
    p.add_argument("--reason")
    cmd("backups", lifecycle.cmd_backups, "list backups, uninstall archives and exports")
    p = cmd("restore", lifecycle.cmd_restore, "roll skills back from a backup or export zip")
    p.add_argument("--backup", required=True)
    p.add_argument("--name", nargs="*")
    p.add_argument("--preview", action="store_true")
    p.add_argument("--reason")
    p.add_argument("--rationale", help="the user's reason for the rollback")
    p = cmd("new", lifecycle.cmd_new, "create a skill from the template")
    p.add_argument("--name", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--purpose")

    # health
    p = cmd("validate", health.cmd_validate, "health check")
    p.add_argument("--name", nargs="*")
    p.add_argument("--path", help="validate a folder that isn't installed (e.g. staged)")
    cmd("cost", health.cmd_cost, "context token estimates")
    p = cmd("trigger-test", health.cmd_trigger_test, "run prompts through the claude CLI and see which skill starts (costs usage)")
    p.add_argument("--prompt", action="append", required=True)
    p.add_argument("--expect")
    p.add_argument("--expect-not", action="store_true")
    p.add_argument("--max-turns", type=int, default=1)
    p.add_argument("--timeout", type=int, default=180)

    # claude.ai and plugins
    cmd("where", remote.cmd_where, "where every skill is active: Claude chat and/or Claude Code")
    cmd("sync-remote", remote.cmd_sync_remote, "log changes to claude.ai account skills and app plugins")
    p = cmd("pull-claude-ai", remote.cmd_pull_claude_ai, "make an editable copy of a claude.ai account skill")
    p.add_argument("--name", required=True)
    p.add_argument("--replace", action="store_true")
    p = cmd("package", remote.cmd_package, "check and zip a local skill or editable claude.ai copy for upload")
    p.add_argument("--name", required=True)
    p.add_argument("--force", action="store_true", help="build the zip even with blockers")

    # portability
    p = cmd("export", portability.cmd_export, "export skills, log and dashboard to the sync folder")
    p.add_argument("--dest")
    p.add_argument("--report")
    p = cmd("import-log", portability.cmd_import_log, "merge the log from an export zip")
    p.add_argument("--zip", required=True)
    p = cmd("obsidian-note", portability.cmd_obsidian_note, "write the skills log and dashboard link into the Obsidian note and set its revision date and time")
    p.add_argument("--path", help="note path (default: obsidian_note in config.json)")
    p = cmd("notes-status", portability.cmd_notes_status, "list skills missing from or stale in the skills notes folder, and each note's revision date")
    p = cmd("dashboard", portability.cmd_dashboard, "write the HTML dashboard")
    p.add_argument("--out")
    p = cmd("publish-repo", publish.cmd_publish_repo, "sync published skills into the GitHub repo clone (sanitized); --push commits and pushes")
    p.add_argument("--push", action="store_true")
    p.add_argument("--message")

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
