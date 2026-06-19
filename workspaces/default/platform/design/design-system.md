# Design System: Agent Context Build Flow

## Flow

1. The maintainer selects a workspace and optional packs.
2. contextd resolves deterministic source knowledge.
3. contextd builds a task artifact with selected docs, gaps, warnings, source hashes, and budget reporting.
4. The agent consumes the artifact through CLI, adapter export, or MCP.

## Accessibility

- The markdown render must remain readable without custom styling.
- Error and gap messages should name the missing path or unsafe input directly.

## UX Writing

Use build-system language: build, explain, validate, and evaluate agent inputs. Avoid implying that contextd is a chat memory or an autonomous orchestrator.

## Edge Cases

- If a pack retrieval map points outside the workspace, skip it and record a security-policy gap.
- If Linux arm64 users request a prebuilt binary, explain that source install is currently required.
