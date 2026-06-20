# Comparison and Positioning

contextd is a governed build layer for AI agent inputs. It is designed to coexist with agent clients, MCP servers, code intelligence tools, and team knowledge bases without becoming any one of them.

## Short Version

| Tool category | What it is good at | Where contextd fits |
|---|---|---|
| MCP | Standard protocol surface for tools, resources, and prompts. | contextd can expose its build engine over MCP, but MCP is not the source of truth. |
| Code graph / code intelligence tools | Fast structural answers about code: symbols, calls, routes, dependencies, impact. | contextd decides which team knowledge, contracts, policies, and workspace docs should guide the task. |
| Cursor rules / Claude memory | Client-native persistent instructions. | contextd exports adapter-specific surfaces from one canonical workspace model. |
| Vector DB / knowledge base | Broad retrieval over large corpora. | contextd builds deterministic context artifacts with explicit gaps, budgets, and source hashes. |

## contextd vs MCP

MCP is a transport and capability protocol. It tells clients how to call tools, read resources, and fetch prompts. It does not define a team's context lifecycle, workspace isolation model, policy checks, pack semantics, or deterministic task artifact.

contextd uses MCP as one adapter surface. The canonical model remains `.contextd/config.json`, workspace knowledge, packs, policies, and `contextd_task_context.v1`.

## contextd vs Code Graph Tools

Code graph tools are excellent when the question is structural:

- Which function calls this?
- What route handles this endpoint?
- What files are affected by this diff?
- Which services are connected?

contextd is for the governance layer around that work:

- Which contract must the agent follow?
- Which workspace is allowed for this codebase?
- Which pack rules apply?
- Which product, requirement, design, runbook, or policy docs are required?
- What context was selected, dropped, or missing?

These tools can complement each other. A code intelligence result can become evidence or workspace knowledge. It should not silently replace the deterministic context artifact.

## contextd vs Cursor Rules and Claude Memory

Client-native rules are convenient, but they tend to become client-specific instruction surfaces. contextd treats those surfaces as exports from a canonical model:

- Claude Code slash commands and agents are adapters.
- Codex skills and instructions are adapters.
- Cursor rules are adapters.
- MCP tools/resources/prompts are adapters.

The build source remains the workspace and pack model, not a single client memory file.

## contextd vs Vector DBs and Knowledge Bases

Vector search is useful for discovery, especially when users do not know what exists. contextd keeps search advisory because governed agent inputs need stricter properties:

- deterministic selection
- workspace isolation
- explicit gaps instead of guessed context
- source hashes
- policy and pack validation
- token-budget reporting

The goal is not to retrieve the most text. The goal is to build the right task input.

## Product Boundary

contextd should not become a code graph indexer, memory database, hosted control plane, agent orchestrator, or vector retrieval system. Its durable role is the build system that turns maintained team knowledge into reliable, inspectable agent inputs.
