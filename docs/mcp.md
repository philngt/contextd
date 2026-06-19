# MCP Adapter

contextd ships a stdlib-only MCP stdio server. It is another adapter over the same deterministic CLI/runtime engine; it does not add a queue, worker runtime, remote transport, or orchestration layer.

The implementation targets the MCP `2025-11-25` stdio flow:
- stdio transport with newline-delimited JSON-RPC messages.
- server capabilities: tools, read-only resources, and prompts.
- methods: `initialize`, `notifications/initialized`, `tools/list`, `tools/call`, `resources/list`, `resources/read`, `prompts/list`, `prompts/get`.

References: [MCP transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) and [MCP tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).

## Start the Server

```bash
contextd mcp-server --knowledge-root ~/contextd --workspace default
```

For team knowledge repos:

```bash
contextd mcp-server --knowledge-root ~/company-wiki --workspace shared
```

`--knowledge-root` must point to a directory containing `workspaces/`. `--workspace` is optional if the MCP client runs inside a project that already resolves via `.contextd/config.json`.

## Generate Client Snippets

```bash
contextd mcp-config --client codex --knowledge-root ~/contextd --workspace default
contextd mcp-config --client claude --knowledge-root ~/contextd --workspace default
contextd mcp-config --client cursor --knowledge-root ~/contextd --workspace default
contextd mcp-config --client all --knowledge-root ~/contextd --workspace default
```

The installer can print the same snippets without editing client MCP config files:

```bash
bash scripts/install-to-claude.sh --knowledge-root ~/contextd --print-mcp-config codex
```

### Codex

Add the generated TOML to your Codex config:

```toml
[mcp_servers.contextd]
command = "contextd"
args = ["mcp-server", "--knowledge-root", "/absolute/path/to/contextd", "--workspace", "default"]
```

### Claude / Cursor

Add the generated JSON to the client MCP config location used by your client:

```json
{
  "mcpServers": {
    "contextd": {
      "command": "contextd",
      "args": [
        "mcp-server",
        "--knowledge-root",
        "/absolute/path/to/contextd",
        "--workspace",
        "default"
      ]
    }
  }
}
```

## Tools

| Tool | Inputs | Output |
|---|---|---|
| `contextd.resolve` | `cwd?` | Resolver JSON with config, workspace, `knowledge_root`, packs, warnings. |
| `contextd.find` | `query`, `workspace?`, `limit?`, `cwd?` | Advisory fuzzy matches. Search never overrides deterministic contracts or patterns. |
| `contextd.context` | `task`, `workspace?`, `cwd?`, `materialize? = false` | Canonical `contextd_task_context.v1` JSON artifact. |
| `contextd.contract_path` | `contract_id`, `workspace?`, `cwd?` | Resolved contract path via `contract-index.json` and fallback filename lookup. |
| `contextd.bundle` | `workspace?`, `include_packs?`, `include_engine?`, `max_chars?` | Capped markdown bundle, default `max_chars=20000`. |

## Resources

The MCP server exposes read-only resources with fixed `contextd://` URIs:

- Active workspace docs: `contextd://workspace/{workspace}/...`
- Active pack docs: `contextd://pack/{pack}/...`
- Runtime docs: `contextd://docs/context-quality.md`, `contextd://docs/governance.md`, `contextd://docs/pack-validation.md`, `contextd://docs/evaluation.md`, `contextd://docs/mcp.md`
- Materialized current task, when present: `contextd://context/current-task.json` and `contextd://context/current-task.md`

`resources/read` accepts only URIs returned by `resources/list`; it does not map arbitrary paths. Secret-like paths and raw evidence source folders are not exposed as MCP resources.

## Prompts

Prompts are small command-oriented templates for clients that support MCP prompts:

- `contextd.build_task_context`
- `contextd.explain_context`
- `contextd.run_policy_check`

They describe which local `contextd` command to run for the given task. They do not execute tools by themselves.

## Error Semantics

- Malformed JSON-RPC, unsupported methods, invalid request shapes, and unknown tool names return JSON-RPC error objects.
- Valid `tools/call` requests whose execution fails return MCP tool results with `isError: true`.
- Server logs and diagnostics go to stderr. Stdout is reserved for valid newline-delimited JSON-RPC messages.

## Security Notes

- MCP v1 is local stdio only. There is no Streamable HTTP server, remote auth surface, or network listener.
- The server reads knowledge files under the resolved `knowledge_root` and active workspace. Keep sensitive workspaces in private repos.
- `contextd.context` defaults to `materialize=false` so MCP calls do not write `.contextd/context/` unless the client explicitly asks.
- `contextd.bundle` is capped by `max_chars`; clients should request only the context they need.

## Compatibility

Legacy `.claude/wiki.json`, `.Codex/wiki.json`, and `wiki_root` remain resolver adapters during migration. MCP snippets and installer flags use canonical `knowledge_root`.
