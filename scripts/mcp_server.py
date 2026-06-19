#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stdlib-only MCP stdio server for contextd.

The server is intentionally an adapter over existing contextd CLI/runtime
modules. It does not orchestrate work; it exposes deterministic context tools
over newline-delimited JSON-RPC.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

import cmd_bundle  # noqa: E402
import cmd_resolve  # noqa: E402
import contextd_version  # noqa: E402
import contextd_resolver  # noqa: E402
import context_security  # noqa: E402
import find_engine  # noqa: E402
import task_context_engine  # noqa: E402


LATEST_PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_PROTOCOL_VERSIONS = {LATEST_PROTOCOL_VERSION, "2025-06-18"}

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class ToolExecutionError(Exception):
    """Tool-level failure returned as an MCP tool error result."""

    def __init__(self, message: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.payload = payload or {}


@dataclass
class ServerOptions:
    knowledge_root: Optional[Path] = None
    workspace: Optional[str] = None
    cwd: Optional[Path] = None


@dataclass
class ResolvedState:
    resolved: Dict[str, Any]
    knowledge_root: Optional[Path]
    workspace: Optional[str]
    project_dir: Path
    packs: List[str]
    warnings: List[str]


def _version() -> str:
    return contextd_version.get_version(start_path=SCRIPT_DIR.parent)


def _json_dumps(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _send(payload: Dict[str, Any]) -> None:
    sys.stdout.write(_json_dumps(payload) + "\n")
    sys.stdout.flush()


def _error_response(request_id: Any, code: int, message: str,
                    data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    error: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _success_response(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _tool_content(payload: Dict[str, Any], is_error: bool = False) -> Dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, indent=2, ensure_ascii=False),
            }
        ],
        "structuredContent": payload,
        "isError": is_error,
    }


def _require_object(value: Any, name: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _limit(value: Any, default: int, minimum: int = 1, maximum: int = 50) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ToolExecutionError("limit must be an integer") from exc
    return max(minimum, min(maximum, parsed))


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ToolExecutionError("boolean parameter must be true or false")


def _resolve_path(raw: Optional[str]) -> Optional[Path]:
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def _available_workspaces(root: Optional[Path]) -> List[str]:
    if root is None:
        return []
    return contextd_resolver.available_workspaces(root)


def _workspace_packs(root: Path, workspace: str, resolved: Dict[str, Any],
                     workspace_overridden: bool) -> Tuple[List[str], str]:
    if not workspace_overridden:
        return list(resolved.get("packs") or []), str(resolved.get("pack_source") or "resolved")
    workspace_md = root / "workspaces" / workspace / "workspace.md"
    packs, source = cmd_resolve.get_effective_packs({}, workspace_md)
    return packs, source


def resolve_state(options: ServerOptions, cwd: Optional[str] = None,
                  workspace: Optional[str] = None,
                  require_workspace: bool = False) -> ResolvedState:
    start_dir = _resolve_path(cwd) or options.cwd or Path(".").resolve()
    resolved = cmd_resolve.resolve(cwd=start_dir, require_workspace=False)
    warnings = list(resolved.get("warnings") or [])

    root = options.knowledge_root
    if root is None:
        root_raw = resolved.get("knowledge_root") or resolved.get("wiki_root")
        root = _resolve_path(str(root_raw)) if root_raw else None
    else:
        root = root.resolve()
        resolved["knowledge_root"] = str(root)
        resolved["wiki_root"] = str(root)

    selected_workspace = workspace or options.workspace or resolved.get("workspace")
    workspace_overridden = bool(workspace or options.workspace)
    if selected_workspace:
        resolved["workspace"] = selected_workspace

    project_dir_raw = resolved.get("project_dir")
    project_dir = Path(str(project_dir_raw)).expanduser().resolve() if project_dir_raw else start_dir

    if root is not None and selected_workspace:
        ws_dir = root / "workspaces" / selected_workspace
        resolved["workspace_dir"] = str(ws_dir) if ws_dir.is_dir() else None

    if require_workspace:
        if root is None:
            raise ToolExecutionError("Could not resolve knowledge_root.", {
                "warnings": warnings,
            })
        if not root.is_dir():
            raise ToolExecutionError(f"knowledge_root does not exist: {root}", {
                "knowledge_root": str(root),
            })
        if not (root / "workspaces").is_dir():
            raise ToolExecutionError(f"knowledge_root must contain workspaces/: {root}", {
                "knowledge_root": str(root),
            })
        if not selected_workspace:
            raise ToolExecutionError("No workspace resolved.", {
                "available_workspaces": _available_workspaces(root),
                "warnings": warnings,
            })
        ws_dir = root / "workspaces" / selected_workspace
        if not ws_dir.is_dir():
            raise ToolExecutionError(f"Workspace directory not found: {ws_dir}", {
                "workspace": selected_workspace,
                "available_workspaces": _available_workspaces(root),
            })

    packs: List[str] = []
    if root is not None and selected_workspace:
        packs, pack_source = _workspace_packs(root, selected_workspace, resolved, workspace_overridden)
        resolved["packs"] = packs
        resolved["pack_source"] = pack_source
        if root:
            missing = [p for p in packs if not (root / "packs" / p / "pack.yaml").is_file()]
            for pack_name in missing:
                msg = f"Active pack not found: {pack_name}"
                if msg not in warnings:
                    warnings.append(msg)
    resolved["warnings"] = warnings

    return ResolvedState(
        resolved=resolved,
        knowledge_root=root,
        workspace=selected_workspace,
        project_dir=project_dir,
        packs=packs,
        warnings=warnings,
    )


def tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "contextd.resolve",
            "title": "Resolve contextd workspace",
            "description": "Resolve canonical contextd config, workspace, knowledge_root, and active packs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cwd": {"type": "string", "description": "Optional directory to resolve from."},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "contextd.find",
            "title": "Find advisory knowledge",
            "description": "Advisory fuzzy discovery across the active workspace and packs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "workspace": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                    "cwd": {"type": "string"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "name": "contextd.context",
            "title": "Build task context",
            "description": "Build the canonical contextd_task_context.v1 JSON artifact.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "workspace": {"type": "string"},
                    "cwd": {"type": "string"},
                    "materialize": {"type": "boolean", "default": False},
                },
                "required": ["task"],
                "additionalProperties": False,
            },
        },
        {
            "name": "contextd.contract_path",
            "title": "Resolve contract path",
            "description": "Resolve a contract id through contract-index.json and filename fallback.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contract_id": {"type": "string"},
                    "workspace": {"type": "string"},
                    "cwd": {"type": "string"},
                },
                "required": ["contract_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "contextd.bundle",
            "title": "Bundle workspace knowledge",
            "description": "Return a capped markdown bundle for the active workspace.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace": {"type": "string"},
                    "include_packs": {"type": "boolean", "default": False},
                    "include_engine": {"type": "boolean", "default": False},
                    "max_chars": {"type": "integer", "minimum": 1, "maximum": 100000},
                    "cwd": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
    ]


def _validate_no_extra(arguments: Dict[str, Any], allowed: Iterable[str]) -> None:
    extra = sorted(set(arguments) - set(allowed))
    if extra:
        raise ToolExecutionError(f"Unsupported argument(s): {', '.join(extra)}")


def _relative_or_abs(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _mime_type(path: Path) -> str:
    if path.suffix == ".json":
        return "application/json"
    if path.suffix in {".yaml", ".yml"}:
        return "application/yaml"
    if path.suffix == ".txt":
        return "text/plain"
    return "text/markdown"


def _resource_allowed(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix not in {".md", ".json", ".yaml", ".yml", ".txt"}:
        return False
    if context_security.block_reason(path):
        return False
    parts = set(path.parts)
    if {".git", "node_modules", "__pycache__"}.intersection(parts):
        return False
    if "evidence" in parts and "sources" in parts:
        return False
    return True


def _add_resource(resources: Dict[str, Dict[str, Any]], uri: str, path: Path,
                  name: str, description: str) -> None:
    if not _resource_allowed(path):
        return
    resources[uri] = {
        "uri": uri,
        "name": name,
        "description": description,
        "mimeType": _mime_type(path),
        "_path": path,
    }


def _resource_map(options: ServerOptions, cwd: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    state = resolve_state(options, cwd=cwd, require_workspace=True)
    assert state.knowledge_root is not None and state.workspace is not None
    resources: Dict[str, Dict[str, Any]] = {}

    ws_dir = state.knowledge_root / "workspaces" / state.workspace
    for path in sorted(ws_dir.rglob("*")):
        if not _resource_allowed(path):
            continue
        rel = path.relative_to(ws_dir).as_posix()
        _add_resource(
            resources,
            f"contextd://workspace/{state.workspace}/{rel}",
            path,
            f"{state.workspace}/{rel}",
            "Active workspace document",
        )

    for pack in state.packs:
        pack_dir = state.knowledge_root / "packs" / pack
        if not pack_dir.is_dir():
            continue
        for path in sorted(pack_dir.rglob("*")):
            if not _resource_allowed(path):
                continue
            rel = path.relative_to(pack_dir).as_posix()
            _add_resource(
                resources,
                f"contextd://pack/{pack}/{rel}",
                path,
                f"{pack}/{rel}",
                "Active pack document",
            )

    for doc_name in ("context-quality.md", "governance.md", "pack-validation.md", "evaluation.md", "mcp.md"):
        path = state.knowledge_root / "docs" / doc_name
        _add_resource(
            resources,
            f"contextd://docs/{doc_name}",
            path,
            f"docs/{doc_name}",
            "contextd runtime documentation",
        )

    context_dir = state.project_dir / ".contextd" / "context"
    for filename in ("current-task.json", "current-task.md"):
        path = context_dir / filename
        _add_resource(
            resources,
            f"contextd://context/{filename}",
            path,
            f"context/{filename}",
            "Materialized current task artifact",
        )

    return resources


def list_resources(options: ServerOptions, params: Dict[str, Any]) -> Dict[str, Any]:
    _validate_no_extra(params, {"cwd", "cursor"})
    resources = []
    for entry in _resource_map(options, cwd=params.get("cwd")).values():
        public = {k: v for k, v in entry.items() if k != "_path"}
        resources.append(public)
    resources.sort(key=lambda item: item["uri"])
    return {"resources": resources}


def read_resource(options: ServerOptions, params: Dict[str, Any]) -> Dict[str, Any]:
    _validate_no_extra(params, {"uri", "cwd"})
    uri = params.get("uri")
    if not isinstance(uri, str) or not uri:
        raise ValueError("resources/read requires params.uri")
    resources = _resource_map(options, cwd=params.get("cwd"))
    entry = resources.get(uri)
    if not entry:
        raise ValueError(f"Unknown or unavailable resource: {uri}")
    path = entry["_path"]
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": entry["mimeType"],
                "text": path.read_text(encoding="utf-8"),
            }
        ]
    }


def prompt_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "contextd.build_task_context",
            "title": "Build task context",
            "description": "Ask contextd to build the canonical task context artifact.",
            "arguments": [
                {"name": "task", "description": "Task to prepare context for.", "required": True},
                {"name": "workspace", "description": "Optional workspace override.", "required": False},
            ],
        },
        {
            "name": "contextd.explain_context",
            "title": "Explain context",
            "description": "Ask contextd to explain selected, dropped, and missing context.",
            "arguments": [
                {"name": "task", "description": "Task to explain context for.", "required": True},
                {"name": "workspace", "description": "Optional workspace override.", "required": False},
            ],
        },
        {
            "name": "contextd.run_policy_check",
            "title": "Run policy check",
            "description": "Ask contextd to evaluate policy-as-code for a task.",
            "arguments": [
                {"name": "task", "description": "Task to check.", "required": True},
                {"name": "workspace", "description": "Optional workspace override.", "required": False},
            ],
        },
    ]


def get_prompt(params: Dict[str, Any]) -> Dict[str, Any]:
    _validate_no_extra(params, {"name", "arguments"})
    name = params.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("prompts/get requires params.name")
    known = {prompt["name"] for prompt in prompt_definitions()}
    if name not in known:
        raise ValueError(f"Unknown prompt: {name}")
    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise ValueError("params.arguments must be an object")
    task = str(arguments.get("task") or "<task>")
    workspace = str(arguments.get("workspace") or "").strip()
    workspace_flag = f" --workspace {workspace}" if workspace else ""
    commands = {
        "contextd.build_task_context": (
            f"Build deterministic context for this task with "
            f"`contextd context {json.dumps(task)}{workspace_flag} --format json --no-materialize`."
        ),
        "contextd.explain_context": (
            f"Explain context selection for this task with "
            f"`contextd explain {json.dumps(task)}{workspace_flag} --format json`."
        ),
        "contextd.run_policy_check": (
            f"Run governance checks for this task with "
            f"`contextd policy-check {json.dumps(task)}{workspace_flag} --format json`."
        ),
    }
    return {
        "description": next(prompt["description"] for prompt in prompt_definitions() if prompt["name"] == name),
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": commands[name],
                },
            }
        ],
    }


def call_tool(name: str, arguments: Dict[str, Any], options: ServerOptions) -> Dict[str, Any]:
    if name == "contextd.resolve":
        _validate_no_extra(arguments, {"cwd"})
        state = resolve_state(options, cwd=arguments.get("cwd"), require_workspace=False)
        payload = dict(state.resolved)
        payload["mcp"] = {
            "advisory": False,
            "knowledge_root_override": str(options.knowledge_root) if options.knowledge_root else None,
            "workspace_override": options.workspace,
        }
        return _tool_content(payload)

    if name == "contextd.find":
        _validate_no_extra(arguments, {"query", "workspace", "limit", "cwd"})
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise ToolExecutionError("query is required")
        state = resolve_state(
            options,
            cwd=arguments.get("cwd"),
            workspace=arguments.get("workspace"),
            require_workspace=True,
        )
        assert state.knowledge_root is not None and state.workspace is not None
        limit = _limit(arguments.get("limit"), default=5, maximum=50)
        results = find_engine.find(
            query,
            state.knowledge_root,
            workspace=state.workspace,
            packs=state.packs,
            limit=limit,
        )
        matches = []
        for score, item in results:
            path = Path(item["path"])
            matches.append({
                "score": score,
                "kind": item["kind"],
                "path": _relative_or_abs(path, state.knowledge_root),
                "absolute_path": str(path),
                "filename": item["filename"],
            })
        return _tool_content({
            "query": query,
            "workspace": state.workspace,
            "knowledge_root": str(state.knowledge_root),
            "advisory": True,
            "limit": limit,
            "matches": matches,
            "warnings": state.warnings,
        })

    if name == "contextd.context":
        _validate_no_extra(arguments, {"task", "workspace", "cwd", "materialize"})
        task = str(arguments.get("task") or "").strip()
        if not task:
            raise ToolExecutionError("task is required")
        state = resolve_state(
            options,
            cwd=arguments.get("cwd"),
            workspace=arguments.get("workspace"),
            require_workspace=True,
        )
        assert state.knowledge_root is not None and state.workspace is not None
        artifact = task_context_engine.build_context_artifact(
            task=task,
            wiki_root=state.knowledge_root,
            workspace=state.workspace,
            packs=state.packs,
            project_dir=state.project_dir,
            warnings=state.warnings,
        )
        if _bool(arguments.get("materialize"), default=False):
            artifact = task_context_engine.materialize_context(artifact, state.project_dir)
        return _tool_content(artifact)

    if name == "contextd.contract_path":
        _validate_no_extra(arguments, {"contract_id", "workspace", "cwd"})
        contract_id = str(arguments.get("contract_id") or "").strip()
        if not contract_id:
            raise ToolExecutionError("contract_id is required")
        state = resolve_state(
            options,
            cwd=arguments.get("cwd"),
            workspace=arguments.get("workspace"),
            require_workspace=True,
        )
        assert state.knowledge_root is not None and state.workspace is not None
        path, warnings = task_context_engine.resolve_contract_path(
            contract_id,
            state.knowledge_root,
            state.workspace,
            state.packs,
        )
        payload = {
            "contract_id": contract_id,
            "workspace": state.workspace,
            "knowledge_root": str(state.knowledge_root),
            "path": str(path) if path else None,
            "relative_path": _relative_or_abs(path, state.knowledge_root) if path else None,
            "warnings": state.warnings + warnings,
        }
        if path is None:
            raise ToolExecutionError(f"Contract not found: {contract_id}", payload)
        return _tool_content(payload)

    if name == "contextd.bundle":
        _validate_no_extra(arguments, {"workspace", "include_packs", "include_engine", "max_chars", "cwd"})
        state = resolve_state(
            options,
            cwd=arguments.get("cwd"),
            workspace=arguments.get("workspace"),
            require_workspace=True,
        )
        assert state.knowledge_root is not None and state.workspace is not None
        max_chars = _limit(arguments.get("max_chars"), default=20000, maximum=100000)
        include_packs = _bool(arguments.get("include_packs"), default=False)
        include_engine = _bool(arguments.get("include_engine"), default=False)
        text = cmd_bundle.bundle(
            workspace=state.workspace,
            max_chars=max_chars,
            include_packs=include_packs,
            include_engine=include_engine,
            cwd=state.project_dir,
            knowledge_root=state.knowledge_root,
            packs_override=state.packs,
        )
        return _tool_content({
            "workspace": state.workspace,
            "knowledge_root": str(state.knowledge_root),
            "include_packs": include_packs,
            "include_engine": include_engine,
            "max_chars": max_chars,
            "truncated": "[TRUNCATED at" in text,
            "content": text,
            "warnings": state.warnings,
        })

    raise ValueError(f"Unknown tool: {name}")


def handle_request(message: Dict[str, Any], options: ServerOptions) -> Optional[Dict[str, Any]]:
    if message.get("jsonrpc") != "2.0" or "method" not in message:
        return _error_response(message.get("id"), INVALID_REQUEST, "Invalid JSON-RPC request")

    method = message["method"]
    request_id = message.get("id")
    is_notification = "id" not in message
    params = message.get("params") or {}
    if params is not None and not isinstance(params, dict):
        return _error_response(request_id, INVALID_PARAMS, "params must be an object")

    if method == "initialize":
        if is_notification:
            return None
        client_version = params.get("protocolVersion") if isinstance(params, dict) else None
        protocol_version = (
            client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS
            else LATEST_PROTOCOL_VERSION
        )
        return _success_response(request_id, {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {
                    "listChanged": False,
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False,
                },
                "prompts": {
                    "listChanged": False,
                },
            },
            "serverInfo": {
                "name": "contextd",
                "title": "contextd",
                "version": _version(),
            },
            "instructions": (
                "contextd exposes deterministic, file-backed workspace context. "
                "Search results are advisory; context artifacts and contracts are canonical."
            ),
        })

    if method == "notifications/initialized":
        return None

    if method == "ping":
        if is_notification:
            return None
        return _success_response(request_id, {})

    if method == "tools/list":
        if is_notification:
            return None
        return _success_response(request_id, {"tools": tool_definitions()})

    if method == "resources/list":
        if is_notification:
            return None
        try:
            return _success_response(request_id, list_resources(options, _require_object(params, "params")))
        except ToolExecutionError as exc:
            return _error_response(request_id, INVALID_PARAMS, str(exc), exc.payload)
        except ValueError as exc:
            return _error_response(request_id, INVALID_PARAMS, str(exc))

    if method == "resources/read":
        if is_notification:
            return None
        try:
            return _success_response(request_id, read_resource(options, _require_object(params, "params")))
        except ToolExecutionError as exc:
            return _error_response(request_id, INVALID_PARAMS, str(exc), exc.payload)
        except ValueError as exc:
            return _error_response(request_id, INVALID_PARAMS, str(exc))

    if method == "prompts/list":
        if is_notification:
            return None
        try:
            _validate_no_extra(_require_object(params, "params"), {"cursor"})
        except ToolExecutionError as exc:
            return _error_response(request_id, INVALID_PARAMS, str(exc), exc.payload)
        return _success_response(request_id, {"prompts": prompt_definitions()})

    if method == "prompts/get":
        if is_notification:
            return None
        try:
            return _success_response(request_id, get_prompt(_require_object(params, "params")))
        except ToolExecutionError as exc:
            return _error_response(request_id, INVALID_PARAMS, str(exc), exc.payload)
        except ValueError as exc:
            return _error_response(request_id, INVALID_PARAMS, str(exc))

    if method == "tools/call":
        if is_notification:
            return None
        try:
            params_obj = _require_object(params, "params")
            tool_name = params_obj.get("name")
            if not isinstance(tool_name, str) or not tool_name:
                return _error_response(request_id, INVALID_PARAMS, "tools/call requires params.name")
            if tool_name not in {tool["name"] for tool in tool_definitions()}:
                return _error_response(request_id, INVALID_PARAMS, f"Unknown tool: {tool_name}")
            arguments = params_obj.get("arguments") or {}
            if not isinstance(arguments, dict):
                return _error_response(request_id, INVALID_PARAMS, "params.arguments must be an object")
            result = call_tool(tool_name, arguments, options)
            return _success_response(request_id, result)
        except ToolExecutionError as exc:
            payload = {
                "error": str(exc),
                **exc.payload,
            }
            return _success_response(request_id, _tool_content(payload, is_error=True))
        except ValueError as exc:
            return _error_response(request_id, INVALID_PARAMS, str(exc))
        except Exception as exc:  # pragma: no cover - defensive protocol boundary
            print(f"contextd mcp-server internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
            return _error_response(request_id, INTERNAL_ERROR, "Internal error")

    if method.startswith("notifications/"):
        return None

    return _error_response(request_id, METHOD_NOT_FOUND, f"Method not found: {method}")


def serve(options: ServerOptions) -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            _send(_error_response(None, PARSE_ERROR, "Parse error", {"detail": str(exc)}))
            continue
        if not isinstance(message, dict):
            _send(_error_response(None, INVALID_REQUEST, "JSON-RPC batch/non-object messages are not supported"))
            continue
        response = handle_request(message, options)
        if response is not None:
            _send(response)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run contextd as a stdio MCP server.")
    parser.add_argument("--knowledge-root", default=None,
                        help="Canonical knowledge_root containing workspaces/")
    parser.add_argument("--workspace", default=None,
                        help="Default workspace for MCP tool calls")
    parser.add_argument("--cwd", default=None,
                        help="Directory used for config resolution and materialization")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    options = ServerOptions(
        knowledge_root=_resolve_path(args.knowledge_root),
        workspace=args.workspace,
        cwd=_resolve_path(args.cwd),
    )
    return serve(options)


if __name__ == "__main__":
    sys.exit(main())
