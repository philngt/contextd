# Runbook: Runtime Adapter Drift

## Symptom

Claude, Codex, Cursor, or plain markdown exports disagree about workspace resolution, referenced docs, context format, or legacy paths.

## Likely Causes

1. An adapter still references `.claude/wiki.json` or `.claude/context/current-task.md` as source of truth.
2. Adapter renderer invents its own context rules instead of consuming task-context JSON.
3. Exported runtime docs omit `.contextd/config.json` or `knowledge_root`.
4. Markdown render was patched manually and diverged from `current-task.json`.

## Diagnosis Steps

```bash
# Build canonical artifact first.
python3 -m scripts.cli context "debug runtime adapter drift" --format json

# Export runtime artifacts to a temp dir.
rm -rf /tmp/contextd-export-smoke
python3 -m scripts.cli export --runtime plain --output /tmp/contextd-export-smoke
python3 -m scripts.cli export --runtime cursor --output /tmp/contextd-export-smoke

# Search adapter docs for stale source-of-truth paths.
rg -n "\\.claude/wiki\\.json|\\.claude/context/current-task\\.md|wiki_root" .claude agents docs README.md QUICKSTART.md
```

Key signals to look for:
- Stale paths are acceptable only in sections labeled Compatibility, Migration, or Legacy adapters.
- All adapters should reference `.contextd/context/current-task.json` as canonical task context.
- Markdown render can be consumed by humans/adapters but must not become source of truth.

## Fix

| Cause | Fix |
|-------|-----|
| Adapter references legacy config as canonical | Update docs/renderers to read `.contextd/config.json` first and label legacy as compatibility. |
| Renderer invents retrieval rules | Change adapter to consume the task-context JSON shape. |
| Markdown divergence | Regenerate via `contextd context`; do not patch `.contextd/context/current-task.md` by hand. |
| Export misses runtime-neutral fields | Add `artifact_type`, `referenced_docs`, `gaps`, `warnings`, `contextPack`, `retrieval_policy`, and `source_hashes`. |

## Verification

```bash
python3 -m scripts.cli context "debug runtime adapter drift" --format json --no-materialize
python3 -m scripts.cli export --runtime plain --output /tmp/contextd-export-smoke
python3 -m scripts.cli export --runtime cursor --output /tmp/contextd-export-smoke
```

Generated adapters should point to the same canonical config and task-context artifact contract.

## Escalation

Escalate if a runtime cannot consume JSON and requires a different context contract. That is a runtime adapter design change, not a docs-only change.

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`) hoặc engine docs được phép retrieve.

- [Task context schema](../../../templates/task-context.schema.json)
- [Multi-agent compatibility mapping](../../../agents/pipeline/multi-agent-pipeline.md)
- [Context artifact generation failure](./context-artifact-generation-failure.md)
