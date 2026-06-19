# Context Artifact Pipeline

## Purpose

Contextd v1 no longer depends on Claude-specific planner/context-selector subagents as the primary runtime. The canonical pipeline is a deterministic CLI artifact builder:

```bash
contextd context "{user_task}" --format json
```

The old multi-agent flow remains useful as design history and as compatibility docs for Claude adapters, but adapters must consume the same JSON shape instead of inventing retrieval rules.

## Canonical Flow

```
User Task
   ↓
[Resolver]              .contextd/config.json → legacy adapters → globals
   ↓
[Intent Classifier]     task type + components + active packs
   ↓
[Retriever]             contracts > patterns > project docs > domain docs
   ↓
[Filter/Slicer]         agents/pipeline/context-filter.md section policies
   ↓
[Validator]             missing refs become gaps; find/RAG stays advisory
   ↓
[Artifact Writer]       .contextd/context/current-task.json
                         .contextd/context/current-task.md
                         .contextd/context/packs/{packKey}.md
   ↓
[Builder/Reviewer]      consume JSON artifact
```

## Artifact Contract

`current-task.json` is the source of truth and uses `artifact_type = "contextd_task_context.v1"`.

Required semantic fields:

- `workspace`
- `intent`
- `referenced_docs`
- `gaps`
- `warnings`
- `contextPack`
- `retrieval_policy`
- `source_hashes`

`current-task.md` is only a render from JSON for humans and runtimes that prefer markdown.

## Compatibility Mapping

| Legacy stage | New owner |
|--------------|-----------|
| Stage 0 resolve `wiki_root` | shared resolver with canonical `knowledge_root` |
| `contextd-planner` | intent classifier inside `contextd context` |
| `contextd-context-selector` | deterministic retriever/slicer/artifact writer |
| `contextd-reviewer` | optional adapter reading `current-task.json` |
| `.claude/context/current-task.md` | `.contextd/context/current-task.json` plus markdown render |

## Runtime Adapter Rule

Claude, Codex, Cursor, and plain exports should all consume the same task-context JSON shape. Adapter-specific prompts may change wording, but they must not change resolution order, doc priority, pack semantics, or workspace isolation.

## Advisory Discovery

`contextd find` and any future RAG/search mode are advisory only. They may suggest docs to inspect, but they do not override deterministic contracts/patterns selected in `referenced_docs`.
