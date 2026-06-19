#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contextd — CLI for the contextd knowledge engine.

Subcommands:
    resolve     Resolve workspace context from cwd
    find        Fuzzy search across workspace knowledge
    bundle      Merge workspace knowledge into a single markdown file
    export      Export workspace knowledge to runtime-specific format
    mcp-server  Run contextd as a stdio MCP tools server
    mcp-config  Print MCP client configuration snippets

Examples:
    contextd resolve
    contextd find "kafka consumer"
    contextd bundle --workspace default --output ./bundle.md --include-packs
    contextd export --runtime plain --workspace default --output ./
    contextd export --runtime codex-plugin --workspace default --output ./
    contextd export --runtime cursor --workspace default --output ./
    contextd context "Add a Kafka consumer for surgery file processed events" --format json
    contextd task-context "Add a Kafka consumer for surgery file processed events" --output ./current-task.md
    contextd mcp-server --knowledge-root ~/contextd --workspace default
    contextd mcp-config --client codex --knowledge-root ~/contextd --workspace default
"""

from __future__ import annotations

import argparse
import importlib.metadata
import sys
from pathlib import Path

try:
    __version__ = importlib.metadata.version("contextd")
except importlib.metadata.PackageNotFoundError:
    try:
        from scripts._version import __version__  # type: ignore
    except ImportError:
        __version__ = "0.0.0-dev"

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import cmd_resolve  # noqa: E402
import cmd_find  # noqa: E402
import cmd_bundle  # noqa: E402
import cmd_task_context  # noqa: E402
import cmd_contract_path  # noqa: E402
import cmd_migrate_config  # noqa: E402
import cmd_mcp_config  # noqa: E402
import mcp_server  # noqa: E402
import render_runtime  # noqa: E402


def _resolve_cmd(args) -> int:
    result = cmd_resolve.resolve(cwd=Path(args.cwd).resolve() if args.cwd else None)
    if args.format == "json":
        import json
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
    parser = argparse.ArgumentParser(
        prog="contextd",
        description="CLI for the contextd knowledge engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # resolve
    p_resolve = sub.add_parser("resolve", help="Resolve workspace context from cwd")
    p_resolve.add_argument("--cwd", default=None, help="Start directory (default: current)")
    p_resolve.add_argument("--format", choices=["json", "text"], default="json",
                           help="Output format (default: json)")
    p_resolve.set_defaults(func=_resolve_cmd)

    # find
    p_find = sub.add_parser("find", help="Fuzzy search across workspace knowledge")
    p_find.add_argument("query", help="Search keywords (space-separated)")
    p_find.add_argument("--workspace", default=None, help="Override workspace name")
    p_find.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    p_find.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
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
    p_context.add_argument("--format", choices=["markdown", "json"], default="json",
                           help="Output format (default: json)")
    p_context.add_argument("--output", default=None, help="Output file path (default: stdout)")
    p_context.add_argument("--output-dir", default=None,
                           help="Project directory for materialized .contextd/context")
    p_context.add_argument("--no-materialize", action="store_true",
                           help="Do not write .contextd/context artifacts")
    p_context.set_defaults(func=_context_cmd)

    # task-context (legacy-compatible alias)
    p_tc = sub.add_parser("task-context", help="Build task context (legacy default: markdown stdout)")
    p_tc.add_argument("task", help="Task description (quote if multi-word)")
    p_tc.add_argument("--workspace", default=None, help="Override workspace name")
    p_tc.add_argument("--format", choices=["markdown", "json"], default="markdown",
                      help="Output format (default: markdown)")
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
    p_contract.add_argument("--format", choices=["text", "json"], default="text")
    p_contract.set_defaults(func=_contract_path_cmd)

    # migrate-config
    p_migrate = sub.add_parser("migrate-config", help="Create .contextd/config.json from legacy config")
    p_migrate.add_argument("--cwd", default=None, help="Start directory (default: current)")
    p_migrate.add_argument("--force", action="store_true", help="Overwrite existing .contextd/config.json")
    p_migrate.add_argument("--dry-run", action="store_true", help="Print config without writing")
    p_migrate.set_defaults(func=_migrate_config_cmd)

    # mcp-server
    p_mcp_server = sub.add_parser("mcp-server", help="Run contextd as a stdio MCP tools server")
    p_mcp_server.add_argument("--knowledge-root", default=None,
                              help="Canonical knowledge_root containing workspaces/")
    p_mcp_server.add_argument("--workspace", default=None,
                              help="Default workspace for MCP tool calls")
    p_mcp_server.add_argument("--cwd", default=None,
                              help="Directory used for config resolution and materialization")
    p_mcp_server.set_defaults(func=_mcp_server_cmd)

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
