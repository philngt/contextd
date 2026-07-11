#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print MCP client configuration snippets for contextd."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import context_security  # noqa: E402
import contextd_resolver  # noqa: E402


VALID_CLIENTS = {"claude", "cursor", "codex", "all"}


def _server_args(knowledge_root: Path, workspace: Optional[str]) -> List[str]:
    args = ["mcp-server", "--knowledge-root", str(knowledge_root)]
    if workspace:
        args.extend(["--workspace", workspace])
    return args


def claude_cursor_snippet(command: str, knowledge_root: Path, workspace: Optional[str]) -> Dict:
    return {
        "mcpServers": {
            "contextd": {
                "command": command,
                "args": _server_args(knowledge_root, workspace),
            }
        }
    }


def codex_snippet(command: str, knowledge_root: Path, workspace: Optional[str]) -> str:
    args = _server_args(knowledge_root, workspace)
    rendered_args = ", ".join(json.dumps(arg) for arg in args)
    return "\n".join([
        "[mcp_servers.contextd]",
        f"command = {json.dumps(command)}",
        f"args = [{rendered_args}]",
    ])


def render(client: str, knowledge_root: Path, workspace: Optional[str] = None,
           command: str = "contextd") -> str:
    """Render one or more client snippets."""
    if client not in VALID_CLIENTS:
        raise ValueError(f"Unsupported MCP client: {client}")

    sections: List[str] = []

    if client in {"claude", "all"}:
        sections.append("# Claude Desktop / Claude Code MCP")
        sections.append(json.dumps(
            claude_cursor_snippet(command, knowledge_root, workspace),
            indent=2,
            ensure_ascii=False,
        ))

    if client in {"cursor", "all"}:
        sections.append("# Cursor MCP")
        sections.append(json.dumps(
            claude_cursor_snippet(command, knowledge_root, workspace),
            indent=2,
            ensure_ascii=False,
        ))

    if client in {"codex", "all"}:
        sections.append("# Codex MCP")
        sections.append(codex_snippet(command, knowledge_root, workspace))

    return "\n\n".join(sections) + "\n"


def run(client: str, knowledge_root: str, workspace: Optional[str] = None,
        command: str = "contextd") -> int:
    root = Path(knowledge_root).expanduser().resolve()
    if not root.is_dir():
        print(f"Error: knowledge_root does not exist: {root}", file=sys.stderr)
        return 1
    try:
        workspaces_root = context_security.confined_child(
            root, "workspaces", "workspaces root", allow_symlink=False
        )
    except ValueError as exc:
        print(f"Error: invalid knowledge_root: {exc}", file=sys.stderr)
        return 1
    if not workspaces_root.is_dir():
        print(f"Error: knowledge_root must contain workspaces/: {root}", file=sys.stderr)
        return 1
    safe_workspace = None
    if workspace is not None:
        safe_workspace, workspace_error = context_security.validate_context_name(
            workspace, "workspace"
        )
        if workspace_error or safe_workspace is None:
            print(f"Error: invalid workspace: {workspace_error}", file=sys.stderr)
            return 1
        try:
            ws_dir = context_security.workspace_dir(root, safe_workspace)
            workspace_md = context_security.confined_child(
                ws_dir, "workspace.md", "workspace.md", allow_symlink=False
            )
        except ValueError as exc:
            print(f"Error: invalid workspace: {exc}", file=sys.stderr)
            return 1
        if not workspace_md.is_file():
            print(f"Error: workspace.md missing: {workspace_md}", file=sys.stderr)
            return 1
        try:
            contextd_resolver.resolve_workspace_packs(
                root, safe_workspace, config={}
            )
        except ValueError as exc:
            print(f"Error: invalid workspace pack state: {exc}", file=sys.stderr)
            return 1

    try:
        sys.stdout.write(render(client, root, workspace=safe_workspace, command=command))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Print contextd MCP client snippets.")
    parser.add_argument("--client", required=True, choices=sorted(VALID_CLIENTS),
                        help="Client snippet to print")
    parser.add_argument("--knowledge-root", required=True,
                        help="Canonical knowledge_root containing workspaces/")
    parser.add_argument("--workspace", default=None,
                        help="Optional default workspace for the MCP server")
    parser.add_argument("--command", default="contextd",
                        help="Command used by the MCP client (default: contextd)")
    args = parser.parse_args()
    sys.exit(run(
        args.client,
        args.knowledge_root,
        workspace=args.workspace,
        command=args.command,
    ))


if __name__ == "__main__":
    main()
