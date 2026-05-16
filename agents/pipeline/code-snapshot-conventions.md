# Code Snapshot Conventions

Quy tắc tạo `raw.md` cho `source_type=code` evidence (output của `/code-analyze`).

> Engine-level. Workspace có thể override bằng `{ws}/evidence/STORAGE.md` (vd thêm rule cho ngôn ngữ khác — Go, Rust, Python).
> Sibling: [raw-storage-conventions.md](raw-storage-conventions.md) (engine-level rules cho mọi source type).

---

## 1. Mục đích

Khi `/code-analyze` chạy trên 1 codebase có sẵn, nó sinh ra **1 evidence** với `source_type=code`. Raw của evidence này KHÔNG phải bản sao source code — đó là **structured metadata snapshot** dạng markdown, đủ cho analysis prompts (CORE-CODE C1–C7) làm việc mà không cần đọc lại codebase.

Lý do KHÔNG copy source code:
- Source code đã có trong git, snapshot tại `git_sha`. Duplicate = 2x storage, conflict-prone.
- Source code thường > 1 MB (vi phạm size limit của raw-storage-conventions.md Section 3).
- Có thể chứa secrets, dump, comments PII — tăng surface attack.

Lý do snapshot metadata vào markdown thay vì query codebase real-time:
- Immutability invariant I-1: raw "đông cứng" tại `git_sha`. Nếu codebase tiến hóa, evidence cũ vẫn cite được context cũ.
- Analysis prompts cần ≤ 200 KB markdown để xử lý gọn (so với grep toàn repo mỗi prompt → tốn time/context).

---

## 2. File layout

```
{ws}/evidence/sources/{evid-id-code}/
├── source.yaml          # source_type=code, git_sha, git_branch, code_scope
├── raw.md               # snapshot metadata theo template templates/code-snapshot.md
└── raw.normalized.md    # auto-tạo nếu raw.md > 50KB (chunk theo Section header)
```

`raw.md` là **markdown ngắn có heading rõ** → theo Section 2 của `raw-storage-conventions.md`, KHÔNG cần `raw.normalized.md` trừ khi vượt 50KB.

---

## 3. evid-id format

**Single-repo** (`--ref`):
```
{YYYY-MM-DD}-code-{slug}
```

`slug` derive theo thứ tự ưu tiên:
1. User pass `--label` → slugify.
2. Project name (từ `pom.xml#artifactId` / `package.json#name`) → slugify.
3. Repo dir name → slugify.

Ví dụ: `2026-05-04-code-surgery-service`.

**Bundle mode** (`--bundle`):
```
{YYYY-MM-DD}-platform-{slug}
```

`slug` = `bundle.yaml#label` → slugify. Prefix `platform` thay `code` để phân biệt trong `_index.md`.

Ví dụ: `2026-05-04-platform-platform-v2`.

Nếu trùng (chạy 2 lần cùng ngày cùng label) → append `-{n}`.

> Note: `git_sha` KHÔNG nằm trong evid-id để tránh ID dài. Audit qua `source.yaml#git_sha` (single-repo) hoặc `source.yaml#code_repos[].git_sha` (bundle). `source_type` vẫn là `code` trong cả hai mode — `/evidence-analyze` chạy CORE-CODE không đổi.

---

## 4. Section structure (bắt buộc)

### Single-repo mode

`raw.md` PHẢI có 10 section sau, theo đúng thứ tự, mỗi section có anchor `#section-N`. Skip section trống bằng dòng `_(none detected)_` — KHÔNG xóa heading.

| # | Heading | Content |
|---|---------|---------|
| 1 | Project metadata | name, version, build tool, language, top dirs, README excerpt |
| 2 | Dependencies | parsed table từ pom.xml / package.json / build.gradle / Cargo.toml / go.mod |
| 3 | Configs | content các file `application.yaml`, `application.properties`, `.env.example` (đã redact) |
| 4 | REST endpoints | grep `@RestController` / `@RequestMapping` / `@GetMapping` / `app.get(` / route DSL |
| 5 | Message consumers | `@KafkaListener`, MQTT subscribers, RabbitMQ listeners, SQS handlers |
| 6 | Services & components | `@Service` / `@Component` / `@Repository` / equivalent stereotypes |
| 7 | DB schema | entities (`@Entity`), repositories, migration files (Flyway/Liquibase) |
| 8 | Public APIs | class signatures cho package-level public API |
| 9 | Git summary | last 50 commits oneline, top contributors, notable commits |
| 10| Notes | observations surprising không fit section nào — kèm citation |

Skeleton: [`templates/code-snapshot.md`](../../templates/code-snapshot.md).

### Bundle mode

Khi `/code-analyze --bundle` chạy, `raw.md` có cấu trúc khác: **Section 0** (overview) ở đầu, sau đó lặp Sections 1–9 cho mỗi repo, cuối cùng là section Docs (nếu có).

**Cấu trúc raw.md bundle**:

```markdown
# Platform Bundle: {label}
Generated: {date} | Repos: {n} | Docs: {m}

## Section 0: Bundle Overview
| Repo | Role | Project | Branch | Git SHA |
|------|------|---------|--------|---------|
| core-framework | framework | com.example:core | main | a1b2c3d |
| shared-libs    | shared-lib | ... | ...  | ...     |

## Repo: core-framework [framework]

### Section 1: Project Metadata [core-framework]
...
### Section 2: Dependencies [core-framework]
...
### Section 3: Configs [core-framework]
...
[Sections 4–9 per repo — với heading suffix `[core-framework]`]

## Repo: shared-libs [shared-lib]
[Sections 1–9 lặp lại]

## Docs

### Doc: Platform Architecture Overview [architecture]
> Source: (docs/architecture.md:L1-L500)
[Key excerpts ≤ 800 chars + citation]

### Doc: External API Spec [openapi]
[Endpoints summary]
```

**Quy tắc bundle**:
- Section 0 BẮT BUỘC (dù chỉ 1 repo) — overview table cho tất cả repo.
- Mỗi section con của repo có heading suffix `[{repo-name}]` để analysis prompts disambiguate.
- Citation dùng prefix repo: `({repo-name}/path/to/file:L..-L..)`. Ví dụ: `(core-framework/src/main/java/SurgeryService.java:L42-L58)`.
- Docs section: tóm tắt key excerpts (≤ 800 chars/doc) — KHÔNG dump toàn bộ file.
- Skip section 10 (Notes) per-repo nếu trống — ghi 1 Notes tổng hợp cuối file thay.

---

## 5. Citation rule

Mọi claim trong `raw.md` PHẢI cite vị trí trong source code thật:

**Single-repo**:
```
({file-path-relative-to-repo}:L<start>-L<end>)
```
Ví dụ: `(src/main/java/com/example/SurgeryController.java:L42-L58)`.

**Bundle mode** — prefix repo-name để disambiguation:
```
({repo-name}/{file-path-relative-to-repo}:L<start>-L<end>)
```
Ví dụ: `(core-framework/src/main/java/SurgeryController.java:L42-L58)`.

Path là **relative tới repo root** (KHÔNG absolute, KHÔNG relative tới `{ws}`). Reason: dễ đọc + tránh leak path nội bộ máy user.

Khi analysis prompts (C1–C7) cite tiếp về raw.md, format chuyển sang `(raw.md#section-N)` hoặc `(raw.md#L..-L..)`.

---

## 6. Config file guard + Redaction rules

### 6.1 Pre-read guard — mặc định BLOCK, phải xin phép

**Nguyên tắc**: `/code-analyze` KHÔNG tự đọc bất kỳ file config nào. Mọi file config trong scope đều bị chặn cho đến khi có một trong hai điều kiện:
- User pass `--allow-configs` flag (cấp phép toàn bộ cho lần chạy này), HOẶC
- User liệt kê file cụ thể trong `--scope` explicit (vd `--scope "application.yaml,src/**"`)

Nếu không có điều kiện nào → Section 3 chứa danh sách file bị skip, không có nội dung.

#### Tầng 1 — Hard blocklist (NEVER READ, ngay cả khi có `--allow-configs`)

Những file này bị chặn vĩnh viễn, không có flag nào bypass được:

| Pattern | Lý do |
|---------|-------|
| `.env` (exact), `.env.local`, `.env.*.local` | Secrets local/prod |
| `*-prod.yaml`, `*-prod.yml`, `*-prod.properties` | Production env |
| `*-production.yaml`, `*-production.yml`, `*-production.properties` | Production env |
| `*secret*.yaml`, `*secret*.yml`, `*secret*.properties` | Tên file explicit secrets |
| `*credential*.yaml`, `*credential*.properties` | Credentials |
| `vault.yaml`, `vault.yml`, `vault.properties` | Vault config |
| `*.key`, `*.pem`, `*.p12`, `*.jks`, `*.pfx`, `*.crt`, `*.cer` | Private keys / certs |
| Bất kỳ file trong `secrets/`, `credentials/`, `.ssh/`, `.gnupg/` | Secret directories |
| `*keystore*`, `*truststore*` | Java keystores |

Nếu khớp blocklist → ghi `[HARD-BLOCKED: {path}]` vào Section 3, không đọc.

#### Tầng 2 — Yêu cầu xác nhận (khi user pass `--allow-configs`)

Khi `--allow-configs` được set, với mỗi file config còn lại (đã qua Tầng 1) → **AskUserQuestion** từng nhóm:

```
📋 Các file config sẽ được đọc vào snapshot:
   1. src/main/resources/application.yaml
   2. src/main/resources/application-dev.yaml
   3. bootstrap.yaml
   4. src/main/resources/application-staging.yaml   ⚠️ staging

Chọn file nào để include (vd "1,2" hoặc "all" hoặc "none"):
Lưu ý: mọi secret sẽ được redact tự động trước khi ghi vào raw.md.
```

User trả lời → chỉ đọc những file được chọn. File bị bỏ qua → ghi `[SKIPPED-BY-USER: {path}]`.

Nếu user muốn xem trước 1 file trước khi quyết định: hiển thị 20 dòng đầu trong conversation (không ghi vào raw.md), sau đó hỏi lại `include / skip`.

#### Ghi chú trong raw.md (Section 3)

Cuối Section 3, luôn append:
```markdown
**Config guard log**
- Included (user approved, after redaction): application.yaml, application-dev.yaml
- Hard-blocked: application-prod.yaml
- Skipped by user: application-staging.yaml, bootstrap.yaml
- Configs not read (--allow-configs not set): application.yaml, ...  ← nếu không có flag
```

---

### 6.2 Post-read redaction (chỉ áp dụng cho file đã được user approve)

#### Section 3 (Configs):
- Tokens, API keys, passwords → `<REDACTED-SECRET>`
- Database URLs có credentials → `jdbc:postgresql://<REDACTED-HOST>/db`
- Internal URLs có credential inline → `<REDACTED-URL>`
- JWT signing keys, encryption keys → `<REDACTED-KEY>`

#### Section 9 (Git summary):
- Email contributors → `Nguyễn A <REDACTED-EMAIL>`
- Commit body chứa sensitive context → redact body, giữ ticket ID

#### NEVER include (bất kỳ section nào):
- File `.env` thật — hard-blocked ở Tầng 1
- `secrets/`, `credentials/` folder — hard-blocked ở Tầng 1
- Output của `kubectl get secrets`, `aws secrets-manager`
- Database dump

Note `notes:` field trong `source.yaml`: `"Configs: {list-included}. Hard-blocked: {list}. Redacted: secrets, emails."`.

Nếu phát hiện secret đã ingest → áp dụng exception I-1 tại `raw-storage-conventions.md` Section 4 (xóa cả folder, audit log).

---

### 6.3 Workspace override blocklist

Workspace có thể thêm entries vào hard blocklist qua `{ws}/evidence/STORAGE.md`. Engine blocklist KHÔNG thể bị thu hẹp (workspace chỉ được add thêm, không được remove):

```markdown
## Config guard — extra hard blocklist for {workspace}
- `application-uat.yaml`            # UAT env có real user data
- `infrastructure/db-config.yaml`   # legacy config chứa creds
```

---

## 7. Size limits

`raw.md` thường nhỏ (10–80 KB cho project trung bình). Limit:

| Mode | Size | Action |
|------|------|--------|
| Single-repo | ≤ 50 KB | OK, không cần `raw.normalized.md` |
| Single-repo | 50 KB < size ≤ 200 KB | Tạo `raw.normalized.md` chunk theo Section heading |
| Single-repo | > 200 KB | STOP — code_scope quá rộng. Chia evidence: `--scope` từng module riêng |
| Bundle | ≤ 50 KB | OK |
| Bundle | 50 KB < size ≤ 300 KB | Tạo `raw.normalized.md` |
| Bundle | > 300 KB | STOP — bundle quá lớn. Bỏ bớt repo hoặc hẹp scope từng repo |

Tip giảm size (bundle mode): dùng `scope: ["src/main/**"]` thay vì `src/**` cho mỗi repo trong `bundle.yaml`; ignore `target/`, `node_modules/`, `dist/`, generated code. Docs section đóng góp nhỏ (≤ 800 chars/doc).

---

## 8. git_sha pinning

`source.yaml#git_sha` PHẢI là full SHA (40 ký tự) của HEAD lúc snapshot. Lý do:
- Reproducibility: chạy lại analysis sau 6 tháng vẫn match đúng version code.
- Audit: trace `Affects:` path trong verified-facts.md về dòng code thật bằng `git show {sha}:{file}`.

Nếu repo không phải git (vd download zip) → set `git_sha: "unmanaged-{sha256-of-tree-manifest}"` và note vào `notes`.

Validator V-02 reject nếu `source_type=code` mà `git_sha` null.

---

## 9. Per-language extraction hints

`/code-analyze` dùng heuristic grep-based. Default works cho:

| Language/Framework | Markers cho Section 4–7 |
|--------------------|--------------------------|
| Java + Spring      | `@RestController`, `@*Mapping`, `@KafkaListener`, `@Service`, `@Component`, `@Entity`, `@Repository` |
| Node + Express     | `app.get(`, `app.post(`, `router.<method>`, exports, class definitions |
| Node + NestJS      | `@Controller`, `@Get`, `@Post`, `@Injectable`, `@MessagePattern` |
| Python + FastAPI   | `@app.get`, `@app.post`, `@router.<method>`, Pydantic models |
| Go                 | `http.HandleFunc`, `gin.GET`, `mux.HandleFunc`, struct tags |

Nếu codebase dùng framework khác / DSL custom → workspace nên thêm rule trong `{ws}/evidence/STORAGE.md`:

```markdown
# {ws}/evidence/STORAGE.md (override)

## Code extraction additions for {workspace}

- Mark REST endpoints: grep `[CustomRoute]` annotation in C# files
- Mark consumers: grep `RegisterHandler<` in handler-registration.cs
```

`/code-analyze` đọc file này (nếu tồn tại) và bổ sung markers trước khi grep.

---

## 10. Quick checklist trước khi commit `/code-analyze`

```
[ ] git working tree clean? (snapshot tại HEAD; uncommitted changes sẽ KHÔNG nằm trong snapshot)
[ ] code_scope đã hợp lý? (không quá rộng → raw.md nổ size, không quá hẹp → miss services)
[ ] Config guard: dùng --allow-configs nếu muốn Section 3 có data; mặc định config bị skip
[ ] Nếu --allow-configs: đã review danh sách file hiển thị trước khi chọn include?
[ ] Đã redact configs? (post-read redaction tự động; verify bằng grep "password|secret|token|api_key" trong raw.md)
[ ] Workspace active đúng? (snapshot bind vào workspace_at_ingest)
[ ] git_sha là full SHA? (KHÔNG short SHA, KHÔNG null)
```

Pass mọi mục → snapshot an toàn để analyze.

---

## 11. Bundle mode — quy tắc bổ sung

Áp dụng khi `/code-analyze --bundle <dir>`:

### 11.1 bundle.yaml

- Đặt `bundle.yaml` trong thư mục staging. Dùng `templates/bundle.yaml` làm skeleton.
- Paths trong `bundle.yaml` resolve **relative tới vị trí `bundle.yaml`** (không phải cwd).
- Symlinks trong staging folder được follow (không copy code).
- `label` phải unique trong workspace (kiểm tra `_index.md` trước khi ingest).

### 11.2 Per-repo git dirty check

Nếu 1 trong nhiều repo có uncommitted changes → WARN per-repo (không block toàn bundle). User có thể tiếp tục — snapshot chỉ ghi HEAD của repo đó. Ghi note vào `notes` field của source.yaml: `"Repo {name}: snapshot at HEAD — {N} uncommitted changes excluded"`.

### 11.3 source.yaml khi bundle

- `origin`: `"platform-bundle:{label}@{YYYY-MM-DD}"`.
- `code_repo_path`: đường dẫn tới thư mục bundle (bundle root — audit chỉ).
- `code_scope`: null (scope per-repo nằm trong `code_repos[].scope`).
- `code_repos`: list đầy đủ mỗi repo với `git_sha`, `git_branch`, `scope`, `role`.
- `include_docs`: list docs đi kèm (sau khi resolve absolute path).

### 11.4 Analysis prompts với bundle

Analysis prompts (CORE-CODE C1–C4) không đổi flow — raw.md richer hơn (nhiều repo):
- C1 thấy nhiều `Section 2: Dependencies` → cross-repo version consistency signal.
- C2 thấy endpoints/consumers từ nhiều repo → cross-repo upstream/downstream.
- C3 đánh `[CROSS-REPO:{repo-a}+{repo-b}]` cho pattern lặp ở ≥ 2 repo.
- C4 có thể detect topic naming inconsistency cross-repo.

Xem chi tiết tại [code-analysis-prompts.md](code-analysis-prompts.md) — phần "Bundle mode notes".

---

## 12. Agentic-engine variant (`code_variant: agentic-engine`)

Áp dụng khi codebase target là **agentic-coding engine / plugin** (markdown-heavy: slash commands, sub-agents, prompt templates), KHÔNG phải runtime code repo. Ví dụ: wiki-template, các Claude Code plugin repo, MCP server skeleton.

### 12.1 Khi nào dùng

`/code-analyze` chọn variant `agentic-engine` khi (auto-detect HOẶC user pass `--variant agentic-engine`):

**Auto-detect heuristic** — `repo_path` thoả ≥ 2 trong:
- `agents/**/*.md` tồn tại (≥ 1 file)
- `.claude/commands/**/*.md` tồn tại (≥ 1 file)
- `.claude/agents/**/*.md` tồn tại (≥ 1 file)
- `templates/` có `.md` / `.yaml` / `.json` skeleton (≥ 2 file)
- `.mcp.json` hoặc `mcp.json` tồn tại

**Override**:
- `--variant agentic-engine` → force, kể cả khi auto-detect không đủ.
- `--variant code` → force classic, kể cả khi markers agentic có mặt.
- Nếu BOTH classic markers (build file/.git) AND agentic markers ≥ 2 → STOP và hỏi user qua AskUserQuestion: "Detect cả hai variant. Chọn `code` (analyze runtime) hay `agentic-engine` (analyze prompts/agents)?"

### 12.2 Validation gate (softened)

Variant `agentic-engine` KHÔNG yêu cầu `.git/` hoặc build file. Chỉ cần ≥ 1 trong các markers ở 12.1. Repos không git → `git_sha = "unmanaged-{sha256-of-tree-manifest}"`, `git_branch = "unmanaged"` (giống Section 8).

### 12.3 Default scope

Nếu user không pass `--scope`, variant agentic-engine dùng heuristic:
- `agents/**/*.md`
- `.claude/commands/**/*.md`
- `.claude/agents/**/*.md`
- `templates/**`
- `.mcp.json`, `mcp.json`
- `README.md`, `CLAUDE.md`
- `settings.json`, `.claude/settings.json`, `.claude/settings.local.json` (vẫn bị gate bởi `--allow-configs`)

### 12.4 Section structure (agentic-engine)

Section 1, 2, 3, 9, 10 giữ nguyên cấu trúc Section 4 của file này (project metadata, dependencies, configs, git summary, notes). Section 4–8 ĐỊNH NGHĨA LẠI:

| # | Heading | Content |
|---|---------|---------|
| 1 | Engine metadata | Engine name, purpose excerpt từ `README.md` / `CLAUDE.md` (≤ 300 chars), top-level dirs (1 cấp) |
| 2 | Dependencies | (a) MCP servers từ `mcp.json` / `.mcp.json` — name, command, role; (b) Claude Code version target nếu README/CLAUDE.md có ghi; (c) script-tool deps từ `package.json`/`requirements.txt`/`pyproject.toml` nếu có; (d) external integrations (Obsidian, Confluence, Linear) suy ra từ command list |
| 3 | Configs | Same redaction + guard rules (`--allow-configs`); thường gồm `wiki.json` schemas, `settings.json` (hooks/permissions) |
| 4 | Slash commands | Table of `.claude/commands/*.md`. Mỗi row: `name`, `purpose` (từ first heading + intro), `inputs (args)`, `outputs (file/state changes)`, `mode (interactive/auto)`, citation |
| 5 | Sub-agents & system prompts | Table of `.claude/agents/*.md` + agent definitions trong `agents/**/*.md`. Mỗi row: `name`, `role`, `tools allowed` (nếu khai báo trong frontmatter), `when_to_use` (1 line), citation |
| 6 | Pipeline stages / Modules | Nếu `agents/pipeline/` tồn tại — list mỗi pipeline stage doc với role + thứ tự; else: list functional modules (knowledge dirs như `workspaces/{ws}/platform/`, `workspaces/{ws}/projects/`) + role |
| 7 | Templates | List `templates/*` skeletons. Mỗi row: `name`, `output artifact type` (markdown doc / yaml manifest / json config), `used by` (command/agent reference nếu detect được) |
| 8 | Hooks & settings | Từ `settings.json` / `.claude/settings.json`: hooks (PreToolUse / PostToolUse / Stop / UserPromptSubmit), permissions allowlist patterns, env vars khai báo. KHÔNG đọc `settings.local.json` trừ khi `--allow-configs` + user explicit chọn |
| 9 | Git summary | Same as Section 4.9. Repos không git → ghi `_(unmanaged — no git history)_`, skip table |
| 10 | Notes | Same as Section 4 — observations surprising kèm citation |

### 12.5 evid-id format

```
{YYYY-MM-DD}-engine-{slug}
```

Prefix `engine` thay `code` để phân biệt trong `_index.md`. `source.yaml#source_type` vẫn là `code`; thêm field `code_variant: agentic-engine` để dispatcher chọn đúng prompt set.

Ví dụ: `2026-05-08-engine-wiki-template-bootstrap`.

### 12.6 source.yaml fields

```yaml
source_type: code
code_variant: agentic-engine        # NEW — discriminator cho prompt dispatch
origin: "engine:{name}@{sha7}"      # khác với code:{name}@{sha7}
git_sha: ...                        # full SHA hoặc "unmanaged-{...}"
git_branch: ...                     # hoặc "unmanaged"
code_scope: [...]                   # default heuristic ở 12.3 nếu không pass --scope
code_repo_path: ...
```

`code_variant` field bắt buộc khi variant ≠ default. Default (vắng mặt) → variant = `code`.

### 12.7 Citation rule

Giống Section 5 — `({path}:L<start>-L<end>)` relative tới repo root. Path sample điển hình:
- `(.claude/commands/wiki-setup.md:L42-L58)` — slash command
- `(agents/pipeline/task-to-docs-map.md:L1-L20)` — pipeline stage
- `(templates/service.md:L1-L80)` — template
- `(settings.json:L5-L12)` — hook config

### 12.8 Analysis prompts dispatcher

Khi `source.yaml#code_variant == "agentic-engine"`, `/evidence-analyze` chạy **CORE-AGENTIC** (A1–A4 + CORE 4 + CORE 8) thay vì CORE-CODE.

Xem [code-analysis-prompts.md](code-analysis-prompts.md) — phần "CORE-AGENTIC prompts".

### 12.9 Bundle mode + agentic-engine

Bundle có thể trộn variants — mỗi repo trong `bundle.yaml` có optional field `variant: code | agentic-engine` (default `code`). Auto-detect per-repo nếu vắng mặt. raw.md bundle vẫn theo Section 4 bundle layout, nhưng per-repo Section 4–8 dùng schema tương ứng variant của repo đó. Heading suffix `[{repo-name}]` giữ nguyên.
