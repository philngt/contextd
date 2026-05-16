# Report Prompts — Wiki → Technical Report (HTML)

Hướng dẫn cho main agent khi sinh **technical report HTML** từ wiki của workspace active. Áp dụng cho `/wiki-report`. Output là 1 file HTML self-contained.

**Templates** (đọc trước khi compose, đảm bảo agent KHÔNG tự design HTML từ đầu):
- [`templates/report-html-skeleton.html`](../../templates/report-html-skeleton.html) — outer shell (CSS + JS + 7 placeholder section + `<dialog>` markdown preview)
- [`templates/report-fragments.html`](../../templates/report-fragments.html) — copy/paste fragments (citation, badges, details, section blocks, ADR rows…). Đọc 1 lần đầu pipeline, dùng lại trong toàn bộ generation.

**Skeleton tự handle**:
- Sidebar nav active highlight + smooth scroll
- Markdown dialog preview: click vào bất kỳ link `.md` (`<a class="cite">` hoặc inline `<a href="../...md">`) → JS bắt event → tra `MD_CACHE` (JSON inline) → render mini-markdown vào `<dialog>` → ESC hoặc click backdrop để đóng. Cache key = path relative từ workspace root. Agent CHỈ cần điền `{{MD_CACHE_JSON}}` placeholder.

> **Workflow mong muốn**: agent KHÔNG compose HTML thủ công từng tag. Cách dùng:
> 1. Đọc skeleton + fragments file 1 lần ở Bước 4.
> 2. Cho mỗi section, copy fragment phù hợp, replace `{{PLACEHOLDER}}` bằng giá trị thực.
> 3. Concat các fragment đã fill → đặt vào placeholder của skeleton.
> 4. Markdown→HTML chỉ áp cho `{{*_BODY}}` placeholders (nội dung từ file `.md`).

---

## Nguyên tắc cốt lõi

1. **No hallucination** — mọi câu trong report PHẢI được suy ra từ file trong `{ws}/`. Không có data → ghi `<p class="nodata">No data in this workspace.</p>`. KHÔNG đoán, không suy diễn ngoài file.
2. **Citation bắt buộc** — mỗi block content (paragraph dài, table, code block) kèm 1 hoặc nhiều `<a class="cite" href="{path-from-workspace-root}">{filename}</a>` ngay sau heading hoặc trước bullet.
3. **Workspace isolation** — chỉ đọc `{ws}/...`. KHÔNG đọc workspace khác. Nếu file wiki link tới workspace khác → để link y nguyên trong text nhưng KHÔNG fetch nội dung.
4. **Self-contained HTML** — KHÔNG thêm `<link href="http...">`, `<script src="http...">`, `<img src="http...">`. Inline mọi thứ. Nếu wiki có image relative path → giữ link `<a>` thay vì embed.
5. **Conservative** — thà ít content nhưng đúng, hơn nhiều content suy diễn.

---

## Markdown → HTML conversion rules

Khi chuyển nội dung file `.md` sang HTML, áp dụng map sau:

| Markdown | HTML |
|---|---|
| `# H1` | bỏ qua (heading file đã được dùng làm section heading parent) |
| `## H2` | `<h3>` |
| `### H3` | `<h4>` |
| `#### H4+` | `<h5>` |
| `**bold**` | `<strong>` |
| `*italic*` | `<em>` |
| `` `code` `` | `<code>` |
| ```` ```lang ... ``` ```` | `<pre><code>...</code></pre>` (escape HTML entities trong content) |
| `- item` | `<li>` trong `<ul>` |
| `1. item` | `<li>` trong `<ol>` |
| `> blockquote` | `<blockquote>` |
| `[text](path)` | `<a href="{path-resolved-from-workspace-root}">text</a>` |
| GFM table `\| col \|` | `<table>` đầy đủ `<thead><tbody>` |
| Mermaid block (```` ```mermaid ````) | `<pre class="mermaid-fallback">{raw mermaid}</pre>` + note `<p class="mermaid-fallback">Mermaid diagram — view <a href="{file}">source file</a> in markdown viewer to render.</p>` |
| HTML literal trong .md | giữ nguyên (đã là HTML) |
| Front-matter YAML | bỏ qua, KHÔNG render |

**Escape**: mọi text content phải escape `&` `<` `>` `"` `'`. Đặc biệt code blocks.

**Link rewrite**: link relative trong .md (vd `[x](../patterns/y.md)`) → resolve về absolute path từ workspace root (vd `platform/patterns/y.md`), giữ `.md` extension. KHÔNG đổi sang `.html` vì user mở trong file viewer.

---

## Fragment cheat sheet

| Need | Fragment in `report-fragments.html` | Source data |
|---|---|---|
| Chip citation sau heading | `citation` | path + filename |
| Section/sub-section trống | `nodata` | — |
| Badge "Used by" cho contract | `badge-used-by` | services list từ `contract_usage` |
| Badge "Adopted by N" cho pattern có service | `badge-adoption-ok` | services list từ `pattern_adoption` |
| Badge "Not adopted yet" cho pattern không có service | `badge-adoption-none` | — |
| Collapsible block | `details` | summary + body HTML |
| Toàn bộ Overview body | `section-overview` | `workspace.md` parsed |
| 1 row Knowledge Map Summary | `km-row` | group name + count + files |
| 1 project block trong Architecture | `section-arch-project` | knowledge-map.md + services |
| 1 service trong project | `service-details` | service file body |
| 1 entry sidebar nav cho project | `arch-nav-item` | project name + slug |
| 1 contract block | `section-contract` | contract file body + usage badge |
| Index header trong Patterns | `section-pattern-index` | `patterns-index.md` |
| 1 pattern block | `section-pattern` | pattern file body + adoption badge |
| 1 domain block | `section-domain` | domain name + child files |
| 1 file trong 1 domain | `domain-file-block` | file body |
| Bảng summary ADRs | `adr-summary-table` | rows |
| 1 row ADR summary | `adr-summary-row` | id, scope, title, status, path |
| Status badge (3 variants) | `adr-status-badge-{ok,warn,neutral}` | status text |
| 1 ADR full content | `adr-full` | adr body |
| 1 runbook block | `section-runbook` | short desc + body |
| Footer (đã có sẵn trong skeleton) | `footer` (nếu cần override) | — |

## Section composition rules

Mỗi section trong report tương ứng 1 placeholder trong skeleton. Quy tắc cấu trúc và source files dưới đây là contract giữa command và template.

### `{{OVERVIEW_BODY}}` — Overview

**Source files** (theo thứ tự ưu tiên):
- `{ws}/workspace.md` — identity, tech stack, entry points

**Cấu trúc**:
```html
<h3>Identity</h3>
<a class="cite" href="workspace.md">workspace.md</a>
<ul>
  <li><strong>Company:</strong> {value}</li>
  <li><strong>Role:</strong> {value}</li>
  <li><strong>Period:</strong> {value}</li>
</ul>

<h3>Tech Stack</h3>
<ul>...</ul>

<h3>Knowledge Map Summary</h3>
<table>
  <thead><tr><th>Group</th><th>Count</th><th>Files</th></tr></thead>
  <tbody>
    <tr><td>Contracts</td><td>{n}</td><td>{list}</td></tr>
    <tr><td>Patterns</td><td>{n}</td><td>{list}</td></tr>
    <tr><td>Domains</td><td>{n}</td><td>{list}</td></tr>
    <tr><td>Projects</td><td>{n}</td><td>{list}</td></tr>
    <tr><td>ADRs (workspace)</td><td>{n}</td><td>{list}</td></tr>
    <tr><td>Runbooks</td><td>{n}</td><td>{list}</td></tr>
  </tbody>
</table>
```

### `{{ARCHITECTURE_BODY}}` + `{{ARCHITECTURE_NAV}}` — Architecture per project

**Source files** (per project trong `{ws}/projects/`):
- `projects/{p}/knowledge-map.md` — high-level map
- `projects/{p}/services/*.md` — service docs
- `platform/architecture/*.md` — chỉ cho 1 lần ở phần intro

**Cấu trúc**:
```html
<h3>Platform Architecture</h3>
<a class="cite" href="platform/architecture/system-overview.md">system-overview.md</a>
{convert content of system-overview.md, drop H1}

<!-- Loop từng project -->
<h3 id="arch-{project-slug}">Project: {project-name}</h3>
<a class="cite" href="projects/{p}/knowledge-map.md">knowledge-map.md</a>
{convert knowledge-map.md content}

<h4>Services</h4>
<details>
  <summary>{service-name}</summary>
  <div class="details-body">
    <a class="cite" href="projects/{p}/services/{file}.md">{file}.md</a>
    {convert service file content, drop H1}
  </div>
</details>
<!-- ... mỗi service 1 details -->
```

`{{ARCHITECTURE_NAV}}` chứa 1 `<li><a href="#arch-{slug}">{project-name}</a></li>` cho mỗi project.

### `{{CONTRACTS_BODY}}` — Contracts catalog

**Source files**: `{ws}/platform/contracts/*.md` (mỗi file 1 contract).

**Cross-reference** (build trước khi sinh): với mỗi contract file, grep tên file/path trong `{ws}/projects/**/services/*.md` để biết service nào dùng.

**Cấu trúc**:
```html
<!-- per contract -->
<h3>{contract-title from H1 of file}</h3>
<a class="cite" href="platform/contracts/{file}.md">{file}.md</a>
<p><span class="badge">Used by: {service-list}</span></p>  <!-- nếu cross-ref ra -->
{convert file content drop H1}
```

Nếu không có contract nào → `<p class="nodata">No contracts in this workspace.</p>`.

### `{{PATTERNS_BODY}}` — Patterns catalog

**Source files**:
- `{ws}/patterns-index.md` — index nguồn
- `{ws}/platform/patterns/*.md` — mỗi pattern 1 file

**Cross-reference**: grep tên pattern trong `{ws}/projects/**/services/*.md` để build adoption map.

**Cấu trúc**:
```html
<h3>Patterns Index</h3>
<a class="cite" href="patterns-index.md">patterns-index.md</a>
{convert patterns-index.md table content}

<!-- per pattern file -->
<h3>{pattern-title}</h3>
<a class="cite" href="platform/patterns/{file}.md">{file}.md</a>
<p>
  <span class="badge ok">Adopted by: {N} services</span>
  {list service names, mỗi tên là <a href="projects/{p}/services/{f}.md">name</a>}
</p>
{convert file content drop H1}
```

Nếu pattern không có service nào dùng → `<span class="badge warn">Not adopted yet</span>`.

### `{{DOMAINS_BODY}}` — Domain workflows

**Source files**: `{ws}/domains/{domain}/*.md` (chủ yếu `workflow.md`).

**Cấu trúc**:
```html
<!-- per domain -->
<h3>Domain: {domain-name}</h3>
{loop file in domain folder}
  <h4>{filename without .md}</h4>
  <a class="cite" href="domains/{d}/{file}.md">{file}.md</a>
  {convert content drop H1}
{end loop}
```

Mermaid state diagram trong workflow.md → `<pre class="mermaid-fallback">` + note (theo conversion table trên).

### `{{ADRS_BODY}}` — ADR digest

**Source files**:
- `{ws}/decisions/*.md` (workspace-level)
- `{ws}/projects/{p}/decisions/*.md` (project-level)

**Cấu trúc**: build summary table trước, sau đó full content trong `<details>`.

```html
<h3>Summary</h3>
<table>
  <thead><tr><th>ID</th><th>Scope</th><th>Title</th><th>Status</th><th>Source</th></tr></thead>
  <tbody>
    <tr>
      <td>ADR-001</td>
      <td>workspace</td>
      <td>{title from H1}</td>
      <td><span class="badge {ok|warn}">{status}</span></td>
      <td><a href="decisions/ADR-001-...md">file</a></td>
    </tr>
    ...
  </tbody>
</table>

<h3>Full ADRs</h3>
<details><summary>ADR-001 — {title}</summary>
  <div class="details-body">
    <a class="cite" href="decisions/...md">...md</a>
    {full ADR content drop H1}
  </div>
</details>
<!-- ... mỗi ADR 1 details -->
```

**Status detection**: grep `Status:` line trong file. Map: `Accepted|Adopted|Active` → `ok`, `Proposed|Draft` → ``, `Deprecated|Superseded|Rejected` → `warn`.

### `{{RUNBOOKS_BODY}}` — Runbooks index

**Source files**: `{ws}/runbooks/*.md`.

**Cấu trúc**: list + summary first 200 chars + collapse toàn bộ content.

```html
<!-- per runbook -->
<h3>{runbook-title}</h3>
<a class="cite" href="runbooks/{file}.md">{file}.md</a>
<p>{first paragraph or first 200 chars of content}</p>
<details><summary>Full runbook</summary>
  <div class="details-body">{full content drop H1}</div>
</details>
```

---

## Validation checklist (trước khi ghi file)

Main agent phải tự kiểm trước khi `Write`:

- [ ] Mọi placeholder `{{...}}` trong skeleton đã được thay (grep `{{` không còn match)
- [ ] Không có string `<script src=` hoặc `<link href=` chứa `http`/`//` (external resource)
- [ ] Mỗi section có ít nhất 1 `<a class="cite"` HOẶC 1 `<p class="nodata">`
- [ ] Không có nội dung từ workspace khác (grep tên các workspace khác trong file output — phải = 0 match)
- [ ] HTML đóng tag đúng: số `<section` = số `</section>`, `<details>` = `</details>`, `<table>` = `</table>`
- [ ] File size hợp lý (< 2MB) — nếu vượt thì gợi ý user thu hẹp scope (rare cho wiki nhỏ)

Engine validator [validator-rules.md](validator-rules.md) có thêm rule `report-html-self-contained` và `report-citation-required` để check tự động.

---

## Error / edge cases

| Tình huống | Xử lý |
|---|---|
| File `.md` parse lỗi (broken markdown) | render best-effort, ghi note `<!-- parse warning: {file} -->` trong HTML |
| Folder section trống (vd no contracts) | `<p class="nodata">No data in this workspace.</p>` |
| Cùng ngày chạy 2 lần | filename suffix `-{HHMMSS}` để không ghi đè |
| Workspace không có `workspace.md` | STOP với guide chạy `/wiki-setup` hoặc `/new-workspace` |
| File quá lớn (1 file > 100KB) | render đầy đủ, KHÔNG truncate (user muốn full report); nếu tổng output > 5MB thì WARN |
| File có `<script>` inline (vd embed JS demo) | escape thành `&lt;script&gt;` — không exec |

---

## Related

- [`/wiki-report` command](../../.claude/commands/wiki-report.md)
- [HTML skeleton](../../templates/report-html-skeleton.html)
- [Validator rules](validator-rules.md) (rules `report-html-*`)
- [Context retrieval map](task-to-docs-map.md) — cùng convention path scope
