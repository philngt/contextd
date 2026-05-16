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

## Active workspace = thuộc tính của codebase, không phải của wiki

Mỗi codebase (project repo) tự khai báo nó dùng workspace nào trong `<project-root>/.claude/wiki.json`:

```json
{
  "project": "surgery-service",
  "workspace": "example-surgery",
  ...
}
```

Slash commands resolve workspace **theo cwd** khi chạy:

| Thứ tự ưu tiên | Nguồn |
|----------------|-------|
| 1 | `<cwd>/.claude/wiki.json` field `workspace` |
| 2 | `~/.claude/wiki-global.json` field `default_workspace` |
| 3 | Nếu chỉ có 1 workspace trong `workspaces/` → dùng nó |
| 4 | STOP và yêu cầu user `/switch-workspace` hoặc `/wiki-setup` |

> KHÔNG còn file `workspaces/.active` global. Active workspace là per-codebase, không phải per-wiki-repo. Lý do: cùng một wiki-template phục vụ nhiều codebase, mỗi codebase có thể thuộc workspace khác nhau — chạy `/use-wiki` ở 2 codebase khác nhau phải retrieve 2 workspace khác nhau, không phụ thuộc lần `/switch-workspace` gần nhất.

### Khi chạy commands TRONG wiki-template repo

Wiki-template repo cũng có `.claude/wiki.json` của riêng nó (mặc định trỏ về `example-surgery`) để khi user edit nội dung wiki từ ngay repo này, các command vẫn biết workspace nào đang được edit.

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
- `/switch-workspace {name}` — đổi `workspace` field trong `<cwd>/.claude/wiki.json` (tạo file nếu chưa có).
- `/new-workspace {name}` — scaffold workspace mới từ `templates/workspace.md`; tuỳ chọn point `<cwd>/.claude/wiki.json` về workspace mới.
- `/wiki-setup` — tạo `<cwd>/.claude/wiki.json` đầy đủ (project + workspace + patterns + contracts + services).
