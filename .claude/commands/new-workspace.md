# Tạo Workspace Mới

Scaffold một workspace mới trong `{wiki_root}/workspaces/{name}/` từ `templates/workspace.md`.

## Bước 0 — Resolve `wiki_root`

Theo [workspace-resolution.md Profile B](../../agents/pipeline/workspace-resolution.md#profile-b--wiki-root-only-active-workspace-optional). Set: `wiki_json_dir`, `effective_wiki_root`. Nếu cả `wiki.json#wiki_root` và `~/.claude/wiki-global.json#wiki_root` đều thiếu → STOP, hướng dẫn user chạy `bash {wiki-template}/scripts/install-to-claude.sh` trước.

## Bước 1 — Thu thập metadata

Hỏi user (dùng AskUserQuestion nếu chưa rõ):

| Field | Yêu cầu |
|-------|---------|
| `name` | kebab-case, không trùng workspace nào trong `workspaces/` |
| `company` | tên công ty / khách hàng |
| `role` | vị trí của user trong workspace này |
| `period` | YYYY-MM (start) → present hoặc YYYY-MM (end) |
| `stack.languages` | comma-separated |
| `stack.messaging` | kafka / mqtt / rabbit / sqs / none |
| `stack.storage` | postgres / mongo / mysql / redis / ... |
| `packs` | comma-separated pack names hoặc `none`. Vd: `pack-event-driven` nếu có Kafka/MQTT. Catalog: xem `packs/README.md`. |

Nếu user chỉ đưa `name`, dùng default placeholder cho các field khác và đánh dấu "TBD" trong file.

## Bước 2 — Validate

- `workspaces/{name}/` chưa tồn tại. Nếu có → STOP, báo user chọn tên khác.
- `name` chỉ chứa `[a-z0-9-]`. Nếu vi phạm → STOP.
- `templates/workspace.md` tồn tại. Nếu thiếu → STOP, báo user repo bị lỗi.

## Bước 3 — Tạo cấu trúc folder

```
workspaces/{name}/
├── platform/
│   ├── architecture/        # stub README
│   ├── contracts/
│   ├── infrastructure/      # stub README
│   └── patterns/
├── domains/                 # stub README
├── projects/
├── runbooks/                # stub README
├── decisions/
└── agents/                  # rỗng — chỉ tạo nếu workspace cần override
```

Dùng `mkdir -p` (Bash trên Windows: forward slashes ok).

### Bước 3.1 — Stub README cho folder hay rỗng

Để user mới hiểu rõ "folder này dùng làm gì + ví dụ file đầu tiên trông như nào", ghi 4 file `README.md` sau (chỉ ghi nếu file chưa tồn tại):

**`platform/architecture/README.md`**:
```md
# Architecture — system topology

System-level diagrams và topology của workspace này. Vd: service map, deployment topology, data flow tổng thể.

Khác `platform/patterns/` (giải pháp tái sử dụng) và `projects/{p}/services/` (per-service doc) — `architecture/` là góc nhìn **toàn hệ thống**.

Ví dụ file đầu tiên: `system-topology.md`, `data-flow-overview.md`, `service-map.md`.

Xoá README này khi đã có doc thực.
```

**`platform/infrastructure/README.md`**:
```md
# Infrastructure — runtime & deployment

Hạ tầng vận hành: Kafka cluster config, K8s namespaces, DB instance, network policy, secret management.

Khác `platform/contracts/` (schema/API) — `infrastructure/` mô tả **chỗ chạy + cách deploy**, không phải interface giữa service.

Ví dụ file đầu tiên: `kafka-cluster.md`, `k8s-namespaces.md`, `secret-management.md`.

Xoá README này khi đã có doc thực.
```

**`domains/README.md`**:
```md
# Domain workflows — business rules & state machines

Mỗi domain con (vd `surgery/`, `billing/`, `ticket/`) chứa: workflow states, transition rules, business invariants. Khác `platform/` (technical) — đây là **business logic** không phụ thuộc stack.

Ví dụ tạo domain đầu tiên: `mkdir domains/{domain-name}` rồi tạo `domains/{domain-name}/workflow.md` với state machine + transitions.

Xoá README này khi đã có domain thực.
```

**`runbooks/README.md`**:
```md
# Runbooks — incident response procedures

Mỗi runbook = 1 incident type. Format: triệu chứng → diagnosis steps → recovery actions → post-mortem template.

Ví dụ file đầu tiên: `kafka-dlq-stuck.md`, `api-5xx-spike.md`, `db-connection-pool-exhausted.md`.

Xoá README này khi đã có runbook thực.
```

## Bước 4 — Generate workspace.md

Đọc `templates/workspace.md`, thay placeholder bằng metadata ở Bước 1, ghi ra `workspaces/{name}/workspace.md`.

Section `## Packs`:
- Nếu user khai báo packs → render mỗi pack thành 1 list item `- {pack-name}`.
- Nếu user chọn `none` hoặc skip → giữ section trống với comment `(none)` để user dễ thêm sau.
- Validate mỗi pack name có tồn tại trong `{wiki_root}/packs/{name}/pack.yaml` — nếu không → warning, vẫn ghi nhưng cảnh báo user.

## Bước 5 — Generate patterns-index.md trống

Ghi `workspaces/{name}/patterns-index.md` với nội dung:

```md
# Patterns Index — {name}

Quick lookup table for AI agents. Find the pattern name, follow the link, read before generating code.

> Paths are relative to this file (workspace root).

## Platform Patterns

| Pattern | When to Use | Path |
|---------|-------------|------|
| _(empty — thêm khi tạo pattern đầu tiên trong `platform/patterns/`)_ | | |

## Contracts

| Contract | What It Governs | Path |
|----------|----------------|------|
| _(empty)_ | | |

## Domain Workflows

| Domain | Path |
|--------|------|
| _(empty)_ | |
```

## Bước 6 — Hỏi switch cho codebase hiện tại

Hỏi user (AskUserQuestion 2 options):

> "Set workspace `{name}` cho codebase hiện tại (`<cwd>`)?"

- Yes → cập nhật field `workspace = "{name}"` trong `<cwd>/.claude/wiki.json` (tạo file minimal nếu chưa có — xem `/switch-workspace` Bước 3).
- No → in hướng dẫn `/switch-workspace {name}` để dùng sau ở codebase phù hợp.

> Active workspace là per-codebase. Tạo workspace mới KHÔNG tự động set nó làm active ở mọi nơi — phải chạy `/switch-workspace` trong codebase muốn dùng.

## Bước 7 — Confirm

In bảng tóm tắt:

```
✓ Workspace created: {wiki_root}/workspaces/{name}/
  - workspace.md       ({company}, {role})
  - patterns-index.md  (empty)
  - 7 folders          (platform/{arch,contracts,infra,patterns}, domains, projects, runbooks, decisions)
  - 4 stub READMEs     (architecture, infrastructure, domains, runbooks — xoá khi có doc thực)

Active for this codebase: {name | unchanged}    (file: <cwd>/.claude/wiki.json)

Next steps:
  1. Thêm platform contracts vào {wiki_root}/workspaces/{name}/platform/contracts/
  2. Thêm patterns vào workspaces/{name}/platform/patterns/ và update patterns-index.md
  3. Tạo project đầu tiên: workspaces/{name}/projects/{project}/knowledge-map.md (dùng templates/service.md cho service docs)
```
