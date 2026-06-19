#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print MCP client configuration snippets for contextd."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


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
    if not (root / "workspaces").is_dir():
        print(f"Error: knowledge_root must contain workspaces/: {root}", file=sys.stderr)
        return 1

    try:
        sys.stdout.write(render(client, root, workspace=workspace, command=command))
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
