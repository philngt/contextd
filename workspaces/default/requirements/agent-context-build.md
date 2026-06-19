# Requirement: Build Reliable Agent Inputs

## Actor

An AI tooling maintainer preparing a codebase for Claude Code, Codex, Cursor, or MCP clients.

## Trigger

The maintainer needs a repeatable task context for a product or design task, not just coding-rule snippets.

## Business Outcome

Agents receive governed inputs that are explainable, reproducible, and scoped to the active workspace.

## Acceptance Criteria

- Given `pack-product`, `pack-ba`, and `pack-ui-ux` are active for a task, contextd retrieves relevant product, requirement, and design docs.
- The generated artifact remains `contextd_task_context.v1`.
- Any missing placeholder such as `{domain}` becomes an explicit non-blocking gap instead of an inferred path.
