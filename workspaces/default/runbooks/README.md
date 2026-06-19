# Runbooks — contextd operations

Mỗi runbook mô tả một failure mode vận hành của contextd v1. Khi `contextd context` classify task là `incident`, `debug`, hoặc `design` liên quan đến config/runtime artifacts, retriever nên ưu tiên runbook đúng với triệu chứng bên dưới.

| Runbook | Retrieve when |
|---------|---------------|
| [config-resolution-failure.md](config-resolution-failure.md) | `resolve`, `/use-contextd`, hoặc `contextd context` không tìm được `.contextd/config.json`, `workspace`, hoặc `knowledge_root`. |
| [workspace-switch-mismatch.md](workspace-switch-mismatch.md) | Workspace active sai sau `/switch-workspace`, workspace directory thiếu, hoặc pack override không như mong đợi. |
| [context-artifact-generation-failure.md](context-artifact-generation-failure.md) | `contextd context` fail, artifact thiếu field, có blocking gaps, hoặc contract/pattern missing. |
| [materialized-context-pack-stale.md](materialized-context-pack-stale.md) | `.contextd/context/current-task.*` hoặc `packs/{packKey}.md` có vẻ stale sau khi đổi static docs. |
| [runtime-adapter-drift.md](runtime-adapter-drift.md) | Claude/Codex/Cursor/plain export không thống nhất với JSON artifact hoặc còn coi legacy path là canonical. |
| [release-manifest-build-failure.md](release-manifest-build-failure.md) | Release, manifest, PyInstaller, wheel, hoặc version smoke fail từ clean checkout. |
| [team-sync-knowledge-root-failure.md](team-sync-knowledge-root-failure.md) | `/contextd-team-sync` fail vì `knowledge_root` không phải git repo, sai remote, hoặc pull/push conflict. |

## Retrieval Notes

- Runbooks are workspace knowledge: retrieve only from the active workspace.
- Engine docs and active-pack baseline docs may accompany a runbook when referenced by the artifact.
- Advisory search may suggest runbooks, but deterministic contracts/patterns and explicit gaps still decide the task context.
