# Workspaces

## Mục đích

User làm việc ở **nhiều công ty/dự án độc lập**, mỗi nơi có platform, contracts, domain rules, ADRs riêng. Mỗi thư mục con dưới `workspaces/` là **một workspace = một sandbox knowledge** không lẫn vào nhau.

> Knowledge từ workspace A KHÔNG được áp dụng khi đang làm task cho workspace B. Pipeline retrieval bắt buộc scope theo active workspace.

## Cấu trúc một workspace

```
{workspace-name}/
├── workspace.md            # metadata: company, role, stack, period
├── patterns-index.md       # bảng index các pattern trong workspace này
├── platform/
│   ├── architecture/
│   ├── contracts/          # MUST-FOLLOW — priority cao nhất khi retrieve
│   ├── infrastructure/
│   └── patterns/
├── domains/{domain}/       # business rules, workflow, state machine
├── projects/{project}/
│   ├── knowledge-map.md    # entry point cho từng project
│   ├── services/
│   └── decisions/          # ADRs cấp project
├── runbooks/               # incident handling
├── decisions/              # ADRs cấp workspace
└── agents/                 # OPTIONAL — override engine defaults
    ├── constraints.md
    └── pipeline/validator-rules.md
```

## Active workspace = thuộc tính của codebase, không phải của knowledge repo

Mỗi codebase (project repo) tự khai báo nó dùng workspace nào trong `<project-root>/.contextd/config.json`:

```json
{
  "project": "surgery-service",
  "workspace": "example-surgery",
  "knowledge_root": "~/company-context"
}
```

Legacy `<project-root>/.claude/wiki.json` và `<project-root>/.Codex/wiki.json` vẫn được đọc như compatibility adapters trong migration window, nhưng `.contextd/config.json` thắng nếu nhiều config cùng tồn tại.

CLI/slash commands resolve workspace **theo cwd** khi chạy:

| Thứ tự ưu tiên | Nguồn |
|----------------|-------|
| 1 | `<cwd>/.contextd/config.json` field `workspace` |
| 2 | Legacy `<cwd>/.claude/wiki.json` / `<cwd>/.Codex/wiki.json` |
| 3 | `~/.contextd/config.json` field `default_workspace` |
| 4 | Legacy globals `~/.claude/wiki-global.json` / `~/.Codex/wiki-global.json` |
| 5 | STOP và yêu cầu user chạy `contextd migrate-config`, `/switch-workspace`, hoặc `/contextd-setup` |

> KHÔNG còn file `workspaces/.active` global. Active workspace là per-codebase, không phải per-knowledge-repo. Lý do: cùng một knowledge repo phục vụ nhiều codebase, mỗi codebase có thể thuộc workspace khác nhau — chạy `contextd context` ở 2 codebase khác nhau phải retrieve 2 workspace khác nhau, không phụ thuộc lần `/switch-workspace` gần nhất.

### Khi chạy commands TRONG wiki-template repo

Contextd repo cũng có `.contextd/config.json` của riêng nó để khi user edit engine/knowledge seed từ ngay repo này, các command vẫn biết workspace nào đang được edit. Legacy `.claude/wiki.json` có thể còn tồn tại để Claude Code adapters cũ không vỡ.

## Override engine

Các file engine (`agents/system-prompt.md`, `agents/constraints.md`, `agents/pipeline/validator-rules.md` ở root) là **default chung, stack-agnostic**. Pipeline resolve theo thứ tự: engine → packs (additive) → workspace (additive last). Mọi layer đều strict-only — chỉ thêm/làm chặt, không nới lỏng.

Workspace có thể bổ sung rules tại `{ws}/agents/...` (prefix `ws-` cho validator rule, `WS:` cho constraint heading).

Không override `agents/pipeline/task-to-docs-map.md`, `task-to-docs-map.md`, `context-filter.md`, `prompt-template.md`, `multi-agent-pipeline.md` — đây là cơ chế chung, nếu workspace cần khác thì sửa engine.

## Packs (stack-specific knowledge)

Engine core không bias theo stack. Knowledge đặc thù (Kafka/MQTT, REST, frontend, mobile, AI, agentic, ...) sống trong **packs** dưới `packs/{name}/`. Workspace opt-in pack qua section `## Packs` trong `workspace.md`:

```md
## Packs

- pack-event-driven
```

Xem [`../packs/README.md`](../packs/README.md) cho catalog và cơ chế.

## Slash commands liên quan

- `/list-workspaces` — bảng tất cả workspace + đánh dấu workspace của codebase hiện tại.
- `contextd migrate-config` — sinh `<cwd>/.contextd/config.json` từ legacy config hiện có.
- `/switch-workspace {name}` — trong migration window vẫn hỗ trợ legacy adapter; canonical target là `<cwd>/.contextd/config.json`.
- `/new-workspace {name}` — scaffold workspace mới từ `templates/workspace.md`; tuỳ chọn point `<cwd>/.contextd/config.json` về workspace mới.
- `/contextd-setup` — bootstrap config cho codebase; nên tạo `.contextd/config.json` canonical và chỉ giữ legacy files như adapter.

## Team Sharing

By default `contextd` is local-first: all workspaces under `workspaces/` (except `default/`) are git-ignored in the engine repo. To share knowledge with your team, create a separate **knowledge repo** that holds your team's workspaces.

See [docs/team-sync.md](../docs/team-sync.md) for the full guide. In short:

1. **Create a team knowledge repo** from `templates/team-knowledge-repo/`.
2. **Install the engine** with `--knowledge-repo` pointing to your knowledge repo:
   ```bash
   bash scripts/install-to-claude.sh --knowledge-repo ~/company-wiki
   ```
3. **Daily sync** via `/contextd-team-sync {pull|push|status}`.

This keeps the engine (commands, agents, templates) separate from your team's private knowledge, making upstream updates trivial.
