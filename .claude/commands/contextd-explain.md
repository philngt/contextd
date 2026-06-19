# /contextd-explain — Explain Wiki Concepts

Giải thích một khái niệm wiki (pattern, contract, ADR, runbook, term) bằng **plain language**. Mục tiêu: non-tech reader hiểu được trong 2 phút.

> Output in trực tiếp ra console — KHÔNG ghi file (đây là tra cứu nhanh, không phải artifact).
> Khác `/business-view` (sinh document persistent cho audience cụ thể) — `/contextd-explain` là on-the-fly explainer.

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `{topic}` | required | Tên pattern/contract/ADR/term, hoặc đường dẫn file. Vd: `mqtt-topic-contract`, `circuit-breaker`, `ADR-0007`, hoặc `platform/patterns/event-sourcing.md`. |
| `--depth {level}` | optional | `tldr` (1 paragraph) / `short` (default — 1 page) / `deep` (1 page + 3 examples + when-NOT-to-use). |
| `--lang {vi\|en}` | optional | Language. Default: workspace language. |

---

## Bước 0 — Workspace check

Resolve workspace. Set `{ws}`. STOP nếu chưa init.

## Bước 1 — Locate topic

1. Nếu `{topic}` là path → đọc trực tiếp.
2. Nếu là tên → search theo thứ tự ưu tiên:
   - `{ws}/patterns-index.md` lookup table
   - `{ws}/platform/patterns/{topic}.md`, `{ws}/platform/patterns/{topic}-*.md`
   - `{ws}/platform/contracts/{topic}.md`
   - `{ws}/decisions/*{topic}*.md`, `{ws}/projects/*/decisions/*{topic}*.md`
   - `{ws}/runbooks/{topic}.md`
   - `{ws}/domains/{topic}/*.md`
   - Glob fallback: any `*.md` chứa H1 match (case-insensitive substring)
3. Multiple match → AskUserQuestion liệt kê paths cho user chọn.
4. Zero match → STOP với suggestion: "Topic không tìm thấy trong `{ws}`. Có thể đây là engine/pack concept — check `{knowledge_root}/agents/`, `{knowledge_root}/packs/*/`, hoặc tạo doc mới."

## Bước 2 — Read source + cross-references

1. Đọc file source.
2. Extract: H1 title, intro paragraph, all H2 headings, code fence count, link list.
3. Đọc tối đa 3 cross-reference files (link xuất hiện đầu trong source) để có context broader.
4. Identify category: `pattern` / `contract` / `decision` / `runbook` / `domain` / `term`.

## Bước 3 — Translate using plain-language rules

Áp dụng **anti-jargon translation** theo [pack-product coding-rules.md](../../packs/pack-product/agents/coding-rules.md) Translation table.

Bonus rules cho `/contextd-explain`:

| Pattern | Replace with |
|---|---|
| Metaphor reach | Use 1 concrete real-world analogy ("circuit breaker" → "fuse box") |
| Code fence | Skip — chỉ describe what code does in 1 sentence |
| Acronym (DLQ, OAuth, JWT, ...) | Expand on first use + 1-line definition in parentheses |
| Mathematical notation | Avoid; describe behavior |

## Bước 4 — Render output (in vào console, KHÔNG ghi file)

### `--depth tldr`

```
📘 {Topic} — TL;DR

{1 paragraph, ≤ 5 sentences. Plain language. 1 analogy.}

Where to read more: {ws}/{path}
```

### `--depth short` (default)

```
📘 {Topic}

WHAT IT IS
{1-2 paragraphs. Plain language. 1 analogy. Expand acronyms.}

WHY IT EXISTS
{1 paragraph: what problem does this solve, what would happen without it.}

WHEN TO USE
- {Concrete scenario 1}
- {Concrete scenario 2}
- {Concrete scenario 3}

WHEN NOT TO USE
- {Anti-pattern scenario}
- {When alternative is better — name the alternative}

RELATED
- {cross-reference 1 — link path}
- {cross-reference 2}

Source: {ws}/{path}
```

### `--depth deep`

`short` + thêm:

```
EXAMPLES
1. {Real example from {ws}/projects/* if found, else generic}
2. {Second example showing variation}
3. {Edge case example}

GOTCHAS
- {Common mistake 1}
- {Common mistake 2}

VOCABULARY
- {term 1}: {plain-language definition}
- {term 2}: {plain-language definition}
```

## Bước 5 — Validate (in-memory, không block)

Run pack-product `pack-product-jargon-leak` rule trên rendered output:
- Nếu fail → re-run translation step (max 2 retry).
- Nếu vẫn fail sau retry → in output kèm warning "⚠ Output còn {N} jargon term — không thể avoid hoàn toàn cho topic này".

---

## Notes

- **No file output**: kết quả chỉ in console — vì topic & audience thay đổi mỗi lần gọi, không cần persist.
- **Workspace isolation**: chỉ tra cứu trong `{ws}/` (+ engine/pack docs nếu user explicit reference path tới `{knowledge_root}/agents/` hoặc `{knowledge_root}/packs/`).
- **Language**: nếu workspace.md có metadata `language: vi` → output Vietnamese mặc định. Override với `--lang en`.
- **Khác slash command khác**:
  - `/contextd-report` → HTML technical report toàn workspace (engineering audience)
  - `/business-view` → 1 document persistent dịch 1 service/contract cho audience cụ thể
  - `/contextd-explain` → on-the-fly console explainer cho 1 topic, plain language
