#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd — Build system for AI coding-agent context."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

from contextd_version import get_version  # noqa: E402

__version__ = get_version(start_path=SCRIPT_DIR.parent)

import cmd_resolve  # noqa: E402
import cmd_find  # noqa: E402
import cmd_bundle  # noqa: E402
import cmd_task_context  # noqa: E402
import cmd_contract_path  # noqa: E402
import cmd_migrate_config  # noqa: E402
import cmd_doctor  # noqa: E402
import cmd_explain  # noqa: E402
import cmd_pack_validate  # noqa: E402
import cmd_policy_check  # noqa: E402
import cmd_eval  # noqa: E402
import cmd_mcp_config  # noqa: E402
import contextd_resolver  # noqa: E402
import mcp_server  # noqa: E402
import render_runtime  # noqa: E402


@dataclass(frozen=True)
class CommandMeta:
    name: str
    summary: str
    group: str
    audience: str
    advanced: bool = False
    legacy: bool = False
    alias_of: str | None = None


GROUP_LABELS = {
    "daily": "Daily",
    "setup": "Setup / Connect",
    "admin": "Admin / Quality",
    "advanced": "Advanced",
    "legacy": "Legacy",
}

GROUP_ORDER = ["daily", "setup", "admin", "advanced", "legacy"]

COMMANDS = {
    "init": CommandMeta(
        "init",
        "Set up or confirm .contextd/config.json for this codebase",
        "setup",
        "agent-daily",
    ),
    "check": CommandMeta(
        "check",
        "Human-friendly setup and safety check",
        "daily",
        "agent-daily",
        alias_of="doctor",
    ),
    "context": CommandMeta(
        "context",
        "Build a deterministic context artifact for a task",
        "daily",
        "agent-daily",
    ),
    "explain": CommandMeta(
        "explain",
        "Explain why docs were selected, dropped, or marked as gaps",
        "daily",
        "agent-daily",
    ),
    "find": CommandMeta(
        "find",
        "Search workspace knowledge by keyword",
        "daily",
        "agent-daily",
    ),
    "recipes": CommandMeta(
        "recipes",
        "Show short workflows for common jobs",
        "daily",
        "agent-daily",
    ),
    "resolve": CommandMeta(
        "resolve",
        "Show resolved workspace, knowledge root, packs, and config",
        "setup",
        "maintainer",
    ),
    "connect": CommandMeta(
        "connect",
        "Generate MCP config using the current resolved workspace by default",
        "setup",
        "agent-daily",
        alias_of="mcp-config",
    ),
    "migrate-config": CommandMeta(
        "migrate-config",
        "Create canonical config from legacy .claude/.Codex config",
        "setup",
        "maintainer",
    ),
    "doctor": CommandMeta(
        "doctor",
        "Full diagnostic report for config, packs, adapters, and safety",
        "admin",
        "maintainer",
    ),
    "policy-check": CommandMeta(
        "policy-check",
        "Evaluate policy-as-code for a task context",
        "admin",
        "maintainer",
        advanced=True,
    ),
    "pack-validate": CommandMeta(
        "pack-validate",
        "Validate pack API and retrieval maps",
        "admin",
        "maintainer",
        advanced=True,
    ),
    "eval": CommandMeta(
        "eval",
        "Evaluate context selection with golden tasks",
        "admin",
        "maintainer",
        advanced=True,
    ),
    "bundle": CommandMeta(
        "bundle",
        "Merge workspace knowledge into one markdown bundle",
        "advanced",
        "maintainer",
        advanced=True,
    ),
    "export": CommandMeta(
        "export",
        "Export workspace knowledge to runtime-specific files",
        "advanced",
        "maintainer",
        advanced=True,
    ),
    "contract-path": CommandMeta(
        "contract-path",
        "Resolve a contract id to a file path",
        "advanced",
        "maintainer",
        advanced=True,
    ),
    "mcp-config": CommandMeta(
        "mcp-config",
        "Print raw MCP client configuration snippets",
        "setup",
        "maintainer",
        advanced=True,
    ),
    "mcp-server": CommandMeta(
        "mcp-server",
        "Run contextd as a stdio MCP tools server",
        "advanced",
        "maintainer",
        advanced=True,
    ),
    "task-context": CommandMeta(
        "task-context",
        "Legacy alias for context with markdown stdout defaults",
        "legacy",
        "legacy",
        legacy=True,
        alias_of="context",
    ),
}

STARTER_COMMANDS = ["init", "check", "context", "explain", "find", "recipes"]


def _command_line(meta: CommandMeta) -> str:
    suffix = []
    if meta.alias_of:
        suffix.append(f"alias of {meta.alias_of}")
    if meta.legacy:
        suffix.append("legacy")
    if meta.advanced and not meta.legacy:
        suffix.append("advanced")
    marker = f" ({', '.join(suffix)})" if suffix else ""
    return f"  {meta.name:<14} {meta.summary}{marker}"


def _render_starter_help() -> str:
    lines = [
        "contextd — build deterministic context for coding agents",
        "",
        "Start here:",
    ]
    lines.extend(_command_line(COMMANDS[name]) for name in STARTER_COMMANDS)
    lines.extend([
        "",
        "Common examples:",
        '  contextd init',
        '  contextd check',
        '  contextd context "prepare agent context for product requirements" --preview',
        '  contextd explain "prepare agent context for product requirements" --text',
        "",
        "More:",
        "  contextd help --all        Show every command grouped by workflow",
        "  contextd <command> --help  Show flags for one command",
    ])
    return "\n".join(lines) + "\n"


def _render_all_help() -> str:
    lines = [
        "contextd commands",
        "",
        "Use `contextd <command> --help` for command-specific flags.",
    ]
    for group in GROUP_ORDER:
        group_commands = [
            meta for meta in COMMANDS.values()
            if meta.group == group
        ]
        if not group_commands:
            continue
        lines.extend(["", GROUP_LABELS[group] + ":"])
        lines.extend(_command_line(meta) for meta in group_commands)
    return "\n".join(lines) + "\n"


def _render_recipes() -> str:
    return "\n".join([
        "contextd recipes",
        "",
        "First run:",
        "  contextd init",
        "  contextd check",
        "",
        "Daily task:",
        '  contextd context "your task" --preview',
        '  contextd explain "your task" --text',
        "",
        "Debug wrong or missing docs:",
        '  contextd explain "your task" --text',
        '  contextd find "keyword" --limit 5',
        "",
        "Connect an MCP client:",
        "  contextd connect --client codex",
        "  contextd connect --client all --knowledge-root /path/to/contextd --workspace default",
        "",
        "Maintain packs and retrieval quality:",
        "  contextd pack-validate --all --text",
        "  contextd eval --golden --workspace default --text",
    ]) + "\n"


def _add_format_arg(parser, choices, default: str, help_text: str | None = None) -> None:
    parser.add_argument(
        "--format",
        choices=choices,
        default=default,
        help=help_text or f"Output format (default: {default})",
    )
    if "json" in choices:
        parser.add_argument("--json", dest="format", action="store_const", const="json",
                            help="Shortcut for --format json")
    if "text" in choices:
        parser.add_argument("--text", dest="format", action="store_const", const="text",
                            help="Shortcut for --format text")
    if "markdown" in choices:
        parser.add_argument("--markdown", dest="format", action="store_const", const="markdown",
                            help="Shortcut for --format markdown")


def _resolve_cmd(args) -> int:
    result = cmd_resolve.resolve(cwd=Path(args.cwd).resolve() if args.cwd else None)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            if isinstance(value, list):
                print(f"{key}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key}: {value}")
    return 0


def _find_cmd(args) -> int:
    return cmd_find.run(
        query=args.query,
        workspace=args.workspace,
        limit=args.limit,
        fmt=args.format,
    )


def _bundle_cmd(args) -> int:
    try:
        result = cmd_bundle.bundle(
            workspace=args.workspace,
            output_dir=Path(args.output).parent if args.output else None,
            max_chars=args.max_chars,
            include_packs=args.include_packs,
            include_engine=args.include_engine,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(result, encoding="utf-8")
        print(f"Bundle written to: {out_path}")
    else:
        print(result)
    return 0


def _export_cmd(args) -> int:
    try:
        artifacts = render_runtime.render(
            runtime=args.runtime,
            workspace=args.workspace,
            include_engine=args.include_engine,
        )
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.install:
        output_dir = Path.home() / ".agents" / "skills" / "contextd"
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(args.output) if args.output else Path(".")
        output_dir.mkdir(parents=True, exist_ok=True)

    for rel_path, content in artifacts.items():
        if args.install:
            # Skip marketplace manifest; keep only the skill files.
            if rel_path.startswith(".codex-plugin/"):
                continue
            # Strip nested skills/contextd/ prefix so files land directly
            # in ~/.agents/skills/contextd/.
            if rel_path.startswith("skills/contextd/"):
                rel_path = rel_path[len("skills/contextd/"):]
        out_path = output_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"Wrote: {out_path}")

    if args.install:
        print(f"Installed contextd skill to: {output_dir}")
    return 0


def _task_context_cmd(args) -> int:
    if sys.stderr.isatty():
        print("Warning: `task-context` is legacy; use `context` for new scripts.", file=sys.stderr)
    return cmd_task_context.run(
        task=args.task,
        workspace=args.workspace,
        output=args.output,
        fmt=args.format,
        materialize=args.materialize,
        output_dir=args.output_dir,
    )


def _context_cmd(args) -> int:
    return cmd_task_context.run(
        task=args.task,
        workspace=args.workspace,
        output=args.output,
        fmt=args.format,
        materialize=not args.no_materialize,
        output_dir=args.output_dir,
    )


def _help_cmd(args) -> int:
    print(_render_all_help() if args.all else _render_starter_help(), end="")
    return 0


def _recipes_cmd(args) -> int:
    _ = args
    print(_render_recipes(), end="")
    return 0


def _init_cmd(args) -> int:
    start = Path(args.cwd).resolve() if args.cwd else Path(".").resolve()
    selected, _ = contextd_resolver.find_config(start)

    if selected and selected.kind == "contextd":
        resolved = contextd_resolver.resolve(start, require_workspace=True)
        print(f"Already configured: {selected.path}")
        if resolved.get("workspace"):
            print(f"workspace: {resolved['workspace']}")
        if resolved.get("knowledge_root"):
            print(f"knowledge_root: {resolved['knowledge_root']}")
        for warning in resolved.get("warnings") or []:
            print(f"warning: {warning}")
        return 1 if resolved.get("error") else 0

    if selected and "legacy" in selected.kind and "global" not in selected.kind:
        return cmd_migrate_config.run(
            cwd=str(start),
            force=args.force,
            dry_run=args.dry_run,
        )

    workspace = args.workspace or "default"
    raw_root = args.knowledge_root
    project_dir = start

    if raw_root:
        root_path = Path(raw_root).expanduser()
        root = root_path if root_path.is_absolute() else project_dir / root_path
        root = root.resolve()
        stored_root = str(root)
    elif (project_dir / "workspaces" / workspace / "workspace.md").is_file():
        root = project_dir
        stored_root = "."
    elif selected and "global" in selected.kind:
        raw_root = selected.data.get("knowledge_root") or selected.data.get("wiki_root")
        if not raw_root:
            print("Error: global config has no knowledge_root/wiki_root.", file=sys.stderr)
            return 1
        root_path = Path(raw_root).expanduser()
        root = root_path if root_path.is_absolute() else selected.project_dir / root_path
        root = root.resolve()
        stored_root = str(root)
    else:
        print(
            "Error: no local contextd config found and knowledge_root could not be inferred.",
            file=sys.stderr,
        )
        print(
            "Run: contextd init --knowledge-root /path/to/contextd-or-team-knowledge-root "
            f"--workspace {workspace}",
            file=sys.stderr,
        )
        return 1

    workspace_md = root / "workspaces" / workspace / "workspace.md"
    if not workspace_md.is_file():
        print(f"Error: workspace not found: {workspace_md}", file=sys.stderr)
        available = contextd_resolver.available_workspaces(root)
        if available:
            print("Available workspaces: " + ", ".join(available), file=sys.stderr)
        return 1

    payload = {
        "project": project_dir.name,
        "workspace": workspace,
        "knowledge_root": stored_root,
        "packs": None,
    }
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.dry_run:
        print(rendered, end="")
        return 0

    out_path = project_dir / ".contextd" / "config.json"
    if out_path.is_file() and not args.force:
        print(f"Error: {out_path} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote: {out_path}")
    print(f"workspace: {workspace}")
    print(f"knowledge_root: {root}")
    return 0


def _check_cmd(args) -> int:
    return cmd_doctor.run(cwd=args.cwd, fmt=args.format)


def _connect_cmd(args) -> int:
    root = args.knowledge_root
    workspace = args.workspace
    if not root or workspace is None:
        resolved = contextd_resolver.resolve(
            Path(args.cwd).resolve() if args.cwd else None,
            require_workspace=False,
        )
        root = root or resolved.get("knowledge_root") or resolved.get("wiki_root")
        if workspace is None:
            workspace = resolved.get("workspace")

    if not root:
        print(
            "Error: could not resolve knowledge_root. "
            "Pass --knowledge-root /path/to/contextd-or-team-knowledge-root.",
            file=sys.stderr,
        )
        return 1

    print(f"# contextd MCP config for {args.client}")
    print("# Add this snippet to your MCP-capable client configuration.")
    return cmd_mcp_config.run(
        client=args.client,
        knowledge_root=root,
        workspace=workspace,
        command=args.command,
    )


def _contract_path_cmd(args) -> int:
    return cmd_contract_path.run(
        contract_id=args.contract_id,
        workspace=args.workspace,
        fmt=args.format,
    )


def _migrate_config_cmd(args) -> int:
    return cmd_migrate_config.run(
        cwd=args.cwd,
        force=args.force,
        dry_run=args.dry_run,
    )


def _doctor_cmd(args) -> int:
    return cmd_doctor.run(
        cwd=args.cwd,
        fmt=args.format,
    )


def _explain_cmd(args) -> int:
    return cmd_explain.run(
        task=args.task,
        workspace=args.workspace,
        cwd=args.cwd,
        fmt=args.format,
    )


def _policy_check_cmd(args) -> int:
    return cmd_policy_check.run(
        task=args.task,
        workspace=args.workspace,
        cwd=args.cwd,
        fmt=args.format,
    )


def _pack_validate_cmd(args) -> int:
    return cmd_pack_validate.run(
        all_packs=args.all,
        pack=args.pack,
        fmt=args.format,
        cwd=args.cwd,
    )


def _eval_cmd(args) -> int:
    return cmd_eval.run(
        golden=args.golden,
        workspace=args.workspace,
        cwd=args.cwd,
        fmt=args.format,
        output=args.output,
    )


def _mcp_server_cmd(args) -> int:
    argv = []
    if args.knowledge_root:
        argv.extend(["--knowledge-root", args.knowledge_root])
    if args.workspace:
        argv.extend(["--workspace", args.workspace])
    if args.cwd:
        argv.extend(["--cwd", args.cwd])
    return mcp_server.main(argv)


def _mcp_config_cmd(args) -> int:
    return cmd_mcp_config.run(
        client=args.client,
        knowledge_root=args.knowledge_root,
        workspace=args.workspace,
        command=args.command,
    )


def main() -> int:
    raw_args = sys.argv[1:]
    if not raw_args or raw_args in (["--help"], ["-h"]):
        print(_render_starter_help(), end="")
        return 0

    parser = argparse.ArgumentParser(
        prog="contextd",
        description="Build system for AI coding-agent context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # help
    p_help = sub.add_parser("help", help="Show starter or full command help")
    p_help.add_argument("--all", action="store_true",
                        help="Show every command grouped by workflow")
    p_help.set_defaults(func=_help_cmd)

    # recipes
    p_recipes = sub.add_parser("recipes", help="Show common contextd workflows")
    p_recipes.set_defaults(func=_recipes_cmd)

    # init
    p_init = sub.add_parser("init", help="Set up or confirm .contextd/config.json")
    p_init.add_argument("--cwd", default=None, help="Project directory (default: current)")
    p_init.add_argument("--workspace", default="default", help="Workspace name (default: default)")
    p_init.add_argument("--knowledge-root", default=None,
                        help="Knowledge root containing workspaces/ (default: infer from cwd/global)")
    p_init.add_argument("--force", action="store_true",
                        help="Overwrite an existing target config when creating one")
    p_init.add_argument("--dry-run", action="store_true", help="Print config without writing")
    p_init.set_defaults(func=_init_cmd)

    # check
    p_check = sub.add_parser("check", help="Human-friendly alias for doctor --format text")
    p_check.add_argument("--cwd", default=None, help="Start directory (default: current)")
    _add_format_arg(p_check, ["text", "json"], "text")
    p_check.set_defaults(func=_check_cmd)

    # resolve
    p_resolve = sub.add_parser("resolve", help="Resolve workspace context from cwd")
    p_resolve.add_argument("--cwd", default=None, help="Start directory (default: current)")
    _add_format_arg(p_resolve, ["json", "text"], "json")
    p_resolve.set_defaults(func=_resolve_cmd)

    # find
    p_find = sub.add_parser("find", help="Fuzzy search across workspace knowledge")
    p_find.add_argument("query", help="Search keywords (space-separated)")
    p_find.add_argument("--workspace", default=None, help="Override workspace name")
    p_find.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    _add_format_arg(p_find, ["text", "json"], "text")
    p_find.set_defaults(func=_find_cmd)

    # bundle
    p_bundle = sub.add_parser("bundle", help="Bundle workspace knowledge into a single markdown file")
    p_bundle.add_argument("--workspace", default=None, help="Workspace name (default: resolved)")
    p_bundle.add_argument("--output", default=None, help="Output file path (default: stdout)")
    p_bundle.add_argument("--max-chars", type=int, default=None,
                          help="Truncate after N chars")
    p_bundle.add_argument("--include-packs", action="store_true",
                          help="Include active pack constraints and rules")
    p_bundle.add_argument("--include-engine", action="store_true",
                          help="Include engine system prompt and rules")
    p_bundle.set_defaults(func=_bundle_cmd)

    # export
    p_export = sub.add_parser("export", help="Export workspace knowledge to runtime-specific format")
    p_export.add_argument("--runtime", required=True,
                          choices=["plain", "codex-plugin", "codex-instructions", "cursor"],
                          help="Target runtime format")
    p_export.add_argument("--workspace", default=None, help="Workspace name (default: resolved)")
    p_export.add_argument("--output", default=None,
                          help="Output directory (default: current dir)")
    p_export.add_argument("--include-engine", action="store_true",
                          help="Include engine docs (for plain runtime)")
    p_export.add_argument("--install", action="store_true",
                          help="Install exported skill to ~/.agents/skills/contextd/")
    p_export.set_defaults(func=_export_cmd)

    # context
    p_context = sub.add_parser("context", help="Build deterministic task context artifact")
    p_context.add_argument("task", help="Task description (quote if multi-word)")
    p_context.add_argument("--workspace", default=None, help="Override workspace name")
    _add_format_arg(p_context, ["markdown", "json"], "json")
    p_context.add_argument("--output", default=None, help="Output file path (default: stdout)")
    p_context.add_argument("--output-dir", default=None,
                           help="Project directory for materialized .contextd/context")
    p_context.add_argument("--no-materialize", action="store_true",
                           help="Do not write .contextd/context artifacts")
    p_context.add_argument("--preview", dest="no_materialize", action="store_true",
                           help="Preview stdout only; alias for --no-materialize")
    p_context.set_defaults(func=_context_cmd)

    # task-context (legacy-compatible alias)
    p_tc = sub.add_parser("task-context", help="Build task context (legacy default: markdown stdout)")
    p_tc.add_argument("task", help="Task description (quote if multi-word)")
    p_tc.add_argument("--workspace", default=None, help="Override workspace name")
    _add_format_arg(p_tc, ["markdown", "json"], "markdown")
    p_tc.add_argument("--output", default=None, help="Output file path (default: stdout)")
    p_tc.add_argument("--materialize", action="store_true",
                      help="Write .contextd/context/current-task.{json,md} and context pack")
    p_tc.add_argument("--output-dir", default=None,
                      help="Project directory for materialized .contextd/context")
    p_tc.set_defaults(func=_task_context_cmd)

    # contract-path
    p_contract = sub.add_parser("contract-path", help="Resolve a contract id to a file path")
    p_contract.add_argument("contract_id", help="Contract id")
    p_contract.add_argument("--workspace", default=None, help="Override workspace")
    _add_format_arg(p_contract, ["text", "json"], "text")
    p_contract.set_defaults(func=_contract_path_cmd)

    # migrate-config
    p_migrate = sub.add_parser("migrate-config", help="Create .contextd/config.json from legacy config")
    p_migrate.add_argument("--cwd", default=None, help="Start directory (default: current)")
    p_migrate.add_argument("--force", action="store_true", help="Overwrite existing .contextd/config.json")
    p_migrate.add_argument("--dry-run", action="store_true", help="Print config without writing")
    p_migrate.set_defaults(func=_migrate_config_cmd)

    # doctor
    p_doctor = sub.add_parser("doctor", help="Diagnose contextd config, packs, and safety")
    p_doctor.add_argument("--cwd", default=None, help="Start directory (default: current)")
    _add_format_arg(p_doctor, ["text", "json"], "json")
    p_doctor.set_defaults(func=_doctor_cmd)

    # explain
    p_explain = sub.add_parser("explain", help="Explain deterministic task context selection")
    p_explain.add_argument("task", help="Task description (quote if multi-word)")
    p_explain.add_argument("--workspace", default=None, help="Override workspace name")
    p_explain.add_argument("--cwd", default=None, help="Start directory (default: current)")
    _add_format_arg(p_explain, ["text", "json"], "json")
    p_explain.set_defaults(func=_explain_cmd)

    # policy-check
    p_policy = sub.add_parser("policy-check", help="Evaluate policy-as-code for a task context")
    p_policy.add_argument("task", help="Task description (quote if multi-word)")
    p_policy.add_argument("--workspace", default=None, help="Override workspace name")
    p_policy.add_argument("--cwd", default=None, help="Start directory (default: current)")
    _add_format_arg(p_policy, ["text", "json"], "json")
    p_policy.set_defaults(func=_policy_check_cmd)

    # pack-validate
    p_pack_validate = sub.add_parser("pack-validate", help="Validate pack API and retrieval maps")
    pack_group = p_pack_validate.add_mutually_exclusive_group()
    pack_group.add_argument("--all", action="store_true", help="Validate all packs")
    pack_group.add_argument("--pack", default=None, help="Validate a single pack")
    p_pack_validate.add_argument("--cwd", default=None, help="Start directory (default: current)")
    _add_format_arg(p_pack_validate, ["text", "json"], "json")
    p_pack_validate.set_defaults(func=_pack_validate_cmd)

    # eval
    p_eval = sub.add_parser("eval", help="Evaluate context selection with golden tasks")
    p_eval.add_argument("--golden", action="store_true", help="Run golden task fixtures")
    p_eval.add_argument("--workspace", default=None, help="Workspace name (default: resolved)")
    p_eval.add_argument("--cwd", default=None, help="Start directory (default: current)")
    _add_format_arg(p_eval, ["text", "json"], "json")
    p_eval.add_argument("--output", default=None, help="Output report path")
    p_eval.set_defaults(func=_eval_cmd)

    # mcp-server
    p_mcp_server = sub.add_parser("mcp-server", help="Run contextd as a stdio MCP tools server")
    p_mcp_server.add_argument("--knowledge-root", default=None,
                              help="Canonical knowledge_root containing workspaces/")
    p_mcp_server.add_argument("--workspace", default=None,
                              help="Default workspace for MCP tool calls")
    p_mcp_server.add_argument("--cwd", default=None,
                              help="Directory used for config resolution and materialization")
    p_mcp_server.set_defaults(func=_mcp_server_cmd)

    # connect
    p_connect = sub.add_parser("connect", help="Generate MCP config from current workspace")
    p_connect.add_argument("--client", default="codex",
                           choices=sorted(cmd_mcp_config.VALID_CLIENTS),
                           help="Client snippet to print (default: codex)")
    p_connect.add_argument("--knowledge-root", default=None,
                           help="Knowledge root containing workspaces/ (default: resolved)")
    p_connect.add_argument("--workspace", default=None,
                           help="Workspace for MCP server (default: resolved)")
    p_connect.add_argument("--command", default="contextd",
                           help="Command used by the MCP client (default: contextd)")
    p_connect.add_argument("--cwd", default=None, help="Start directory (default: current)")
    p_connect.set_defaults(func=_connect_cmd)

    # mcp-config
    p_mcp_config = sub.add_parser("mcp-config", help="Print MCP client configuration snippets")
    p_mcp_config.add_argument("--client", required=True,
                              choices=sorted(cmd_mcp_config.VALID_CLIENTS),
                              help="Client snippet to print")
    p_mcp_config.add_argument("--knowledge-root", required=True,
                              help="Canonical knowledge_root containing workspaces/")
    p_mcp_config.add_argument("--workspace", default=None,
                              help="Optional default workspace for MCP server")
    p_mcp_config.add_argument("--command", default="contextd",
                              help="Command used by the MCP client (default: contextd)")
    p_mcp_config.set_defaults(func=_mcp_config_cmd)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
