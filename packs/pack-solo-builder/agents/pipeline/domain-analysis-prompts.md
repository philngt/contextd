# Domain Analysis Prompts (4) — Non-tech Override

Override cho CORE 1, 2, 4, 8 của [`critical-analysis-prompts.md`](../../../../agents/pipeline/critical-analysis-prompts.md) khi workspace bật `pack-solo-builder` và source là **domain knowledge** (PDF tiêu chuẩn, paste công thức ngành, doc chuyên môn — KHÔNG phải engineering content).

## Khi nào dùng file này

`/evidence-analyze` Bước 2 detect:
- `source.yaml#source_type` is a non-code text source (`paste`, `api`, `mcp`, `document`, `interview`, `ticket`, `analytics`, `regulation`, `design`, or `incident`)
- Workspace `## Packs` có `pack-solo-builder`
- Workspace KHÔNG có engineering pack active (`pack-event-driven`, `pack-web-api`, `pack-frontend-react`, `pack-ai-app`, `pack-agentic`, `pack-claude-plugin-dev`)

→ Dùng prompts trong file này thay vì critical-analysis-prompts.md CORE.

Nếu workspace mix `pack-solo-builder` + engineering pack → dùng prompts gốc (engineering ưu tiên), nhưng `/evidence-qa` vẫn áp UX adjustments cho non-tech (xem `qa-batch-non-tech.md`).

## Filename mapping

| File output | Prompt thay thế |
|-------------|------------------|
| `01-resource-upload.md` | DOMAIN 1 — Domain Topic Summary |
| `02-contradiction.md`   | DOMAIN 2 — Glossary & Standards Cross-check |
| `04-questions.md`       | DOMAIN 4 — Non-tech Question Generator |
| `08-knowledge-gaps.md`  | DOMAIN 8 — Domain Coverage Gap |

CORE 4 và CORE 8 dùng CHUNG filename với critical pipeline (output schema giống nhau) để `/evidence-qa` và `/evidence-apply` không phân nhánh logic. Body prompt khác.

ON-DEMAND prompts (3, 5, 6, 7, 9, 10) GIỮ NGUYÊN từ critical-analysis-prompts.md — user có thể chạy thủ công nếu muốn.

---

## DOMAIN 1 — Domain Topic Summary

**Output**: `01-resource-upload.md`

**Inputs**:
- `sources/{id}/raw.normalized.md` (full) hoặc `raw.{ext}`
- `sources/{id}/source.yaml`

**Prompt**:
> Tài liệu này thuộc lĩnh vực chuyên môn ({field} — vd cơ khí, kế toán, y tế, luật, giáo dục). Hãy phân tích như chuyên gia ngành đọc cho đồng nghiệp ngành, KHÔNG phải kỹ sư phần mềm.
>
> 1. **3 chủ đề chính** của tài liệu — bằng ngôn ngữ ngành (vd "tính toán moment uốn cho dầm thép", "quy định khấu trừ VAT cho dịch vụ B2B", "phác đồ điều trị tăng huyết áp giai đoạn 1")
> 2. **Loại nội dung** (chọn 1+):
>    - Định nghĩa thuật ngữ (term + nghĩa)
>    - Công thức / công thức tính
>    - Quy tắc / quy định / tiêu chuẩn (JIS/ISO/TCVN/regulation)
>    - Quy trình / phác đồ / SOP
>    - Bảng tra cứu (material properties, drug dosage, ...)
>    - Case study / ví dụ thực tế
> 3. **Ai trong ngành dùng cái này** (vd "kỹ sư thiết kế kết cấu", "kế toán doanh nghiệp", "bác sĩ nội khoa")
> 4. **Có nguồn chính thức không** (tiêu chuẩn, sách giáo khoa, regulation, body authority) — list nếu có
> 5. **Phát hiện đáng chú ý** (≤ 3 mục) — vd term mới, công thức khác baseline ngành, exception ít người biết
>
> Mỗi mục bullet kèm citation `(raw.normalized.md#L{start}-L{end})` hoặc `(raw.md#L...)`.
>
> KHÔNG hỏi về API, schema, deployment, container — đây là tài liệu ngành, không phải code.

**Output schema**:
```markdown
# 01 — Domain Topic Summary

## Chủ đề chính
- {topic 1} (raw.md#L1-L20)
- {topic 2} (raw.md#L21-L40)
- {topic 3} (raw.md#L41-L60)

## Loại nội dung
- {Định nghĩa | Công thức | Quy tắc | Quy trình | Bảng tra | Case study}
  - Cụ thể: {what}

## Audience trong ngành
- {role 1} dùng để {purpose}
- {role 2}

## Nguồn chính thức (nếu có)
- {standard/book/regulation name + version + authority}
- (Nếu không có) → "Không cite nguồn chính thức trong tài liệu"

## Phát hiện đáng chú ý
- {finding 1} (citation)
- {finding 2}
```

---

## DOMAIN 2 — Glossary & Standards Cross-check

**Output**: `02-contradiction.md`

**Inputs**: 01, raw.normalized.md, `{ws}/domains/*/glossary.md` (tất cả file glossary nếu có).

**Prompt**:
> So sánh tài liệu này với glossary hiện có của workspace tại `{ws}/domains/*/glossary.md`.
>
> 1. **Term trùng nhưng định nghĩa khác**:
>    - Term: {term}
>    - Định nghĩa trong raw: {def from raw}
>    - Định nghĩa trong glossary: {def from glossary path}
>    - Mức độ khác: minor (synonymous) | medium (overlap) | major (conflicting)
> 2. **Term mới chưa có trong glossary** — liệt kê + đề xuất section glossary nào để thêm
> 3. **Công thức / quy tắc** trong raw có thể khác với version đã có trong glossary
> 4. **Tiêu chuẩn / regulation** referenced — version mới hơn version trong glossary?
>
> KHÔNG so sánh với `{ws}/platform/contracts/` hoặc `{ws}/platform/patterns/` — đây là engineering scope, không relevant.
>
> Mỗi finding kèm citation cả 2 phía (raw + glossary).

**Output schema**:
```markdown
# 02 — Glossary & Standards Cross-check

## Term conflicts
| Term | Severity | Raw definition | Glossary definition | Glossary path |
|------|----------|----------------|---------------------|---------------|
| {term} | major | (raw.md#L10) ... | (path#L5) ... | domains/co-khi/glossary.md |

## Term mới (đề xuất add)
- {term} → suggest add vào: `{ws}/domains/{field}/glossary.md` section "{section}" (raw.md#L20)

## Công thức / quy tắc khác phiên bản
- {rule}: raw nói X, glossary nói Y → cần verify version (raw.md#L30 + path#L15)

## Tiêu chuẩn / regulation
- {standard}: raw cite version A, glossary có version B → recommend update glossary (raw.md#L40)
```

Nếu workspace KHÔNG có `{ws}/domains/*/glossary.md` → output:
```markdown
# 02 — Glossary & Standards Cross-check

## Status
Workspace chưa có domain glossary. Skip cross-check.

Recommend: create `{ws}/domains/{field}/glossary.md` để track terms ngành.
```

---

## DOMAIN 4 — Non-tech Question Generator

**Output**: `04-questions.md`

**Inputs**: 01, 02, 08 (nếu có), raw.

**Prompt**:
> Tạo câu hỏi cho **chuyên gia ngành** (KHÔNG phải kỹ sư phần mềm) trả lời. Ngôn ngữ plain — tránh jargon kỹ thuật phần mềm.
>
> 1. **8 câu hỏi cốt lõi** (P0/P1) — focus vào:
>    - Term này nghĩa chính xác là gì trong ngành?
>    - Công thức/quy tắc này áp dụng ở case nào? Có exception không?
>    - Có nguồn chính thức (standard/book/regulation) confirm không?
>    - Có version mới hơn không?
>    - Ai trong team/công ty là expert được trust nhất về topic này?
> 2. **5 câu hỏi mở rộng** (P2) — focus vào:
>    - Edge case ít gặp
>    - Liên hệ với term/quy tắc khác trong ngành
>    - Có conflict với practice hiện tại của team không?
> 3. **3 câu game-changer** (P3) — focus vào:
>    - Nếu term/quy tắc này hiểu sai sẽ dẫn tới hậu quả gì?
>    - Có cách tiếp cận khác trong ngành không (vd school of thought khác)?
>
> **TUYỆT ĐỐI KHÔNG hỏi**:
> - "API endpoint nào?" / "Schema database thế nào?" / "Service nào consume?"
> - "Deploy topology?" / "Performance SLA?" / "Container cấu hình?"
> - Bất kỳ câu nào yêu cầu kiến thức kỹ thuật phần mềm.
>
> Mỗi câu có option implicit "Không biết — defer to expert" trong UX `/evidence-qa`.
>
> Format mỗi câu:
> ```
> - [q-XXX] (P0|P1|P2|P3) {question}
>   - reason: {why this priority}
>   - source: {01|02|08|raw|inferred}
>   - expert_hint: {role nào trong ngành thường biết — vd "kỹ sư thiết kế kết cấu senior", "kế toán trưởng", "bác sĩ chuyên khoa"}
> ```

**Output schema**:
```markdown
# 04 — Question Pool (Domain)

## Block 1 — Core questions (8) — focus định nghĩa, áp dụng, nguồn
- [q-001] (P0) {question} — reason: term mới chưa có glossary — source: 02 — expert_hint: {role}

## Block 2 — Extension questions (5) — focus edge case, liên hệ
- [q-009] (P2) ...

## Block 3 — Game-changers (3) — focus hậu quả nếu hiểu sai
- [q-014] (P3) ...
```

---

## DOMAIN 8 — Domain Coverage Gap

**Output**: `08-knowledge-gaps.md`

**Inputs**: 01, raw, `{ws}/domains/*/glossary.md`, `{ws}/domains/*/workflow.md` (nếu có).

**Prompt**:
> Map những gì raw nói ↔ những gì workspace ĐÃ có trong `{ws}/domains/`. Identify gaps.
>
> 1. **Term trong raw KHÔNG có trong workspace glossary** — recommend add (đường dẫn cụ thể).
> 2. **Quy trình/workflow trong raw KHÔNG có trong `{ws}/domains/{field}/workflow.md`** — recommend add (đường dẫn cụ thể).
> 3. **Bảng tra cứu / formula reference** trong raw chưa được capture — recommend section nào trong glossary.
> 4. **Standard/regulation** referenced nhưng wiki chưa cite — recommend add vào "Sources" section của glossary.
>
> KHÔNG hỏi về platform/contracts/patterns gap — đây là domain scope, không phải engineering.

**Output schema**:
```markdown
# 08 — Domain Coverage Gap

## Term gaps
| Term | Found in raw | Suggest add to | Priority |
|------|--------------|----------------|----------|
| {term} | (raw.md#L10) | `{ws}/domains/{field}/glossary.md#{section}` | high|medium|low |

## Workflow gaps
- {workflow name}: raw mô tả (raw.md#L20-L40), workspace chưa có file → suggest tạo `{ws}/domains/{field}/workflow-{slug}.md`

## Formula / reference table gaps
- {table name}: raw có (raw.md#L50), suggest add vào `{ws}/domains/{field}/glossary.md#references`

## Standard / regulation gaps
- {standard name + version}: cited trong raw nhưng workspace chưa track → suggest add vào glossary "Sources" section

## Cross-cutting (nếu có)
- {finding}: ảnh hưởng nhiều domain — recommend tạo `{ws}/domains/cross/{slug}.md`
```

---

## Apply phase

`/evidence-apply` đọc `verified-facts.md` và route theo `Affects:` path. Khi pack-solo-builder active, `Affects:` thường point tới:
- `{ws}/domains/{field}/glossary.md` (term, formula, standard)
- `{ws}/domains/{field}/workflow-{slug}.md` (quy trình)
- `{ws}/tools/{slug}-spec.md` (nếu evidence inform 1 tool spec đang dùng)

KHÔNG route tới `{ws}/platform/` — đó là engineering scope.

## Notes

- Prompts ở đây vẫn cite raw + workspace như critical-analysis-prompts.md → `/evidence-apply` parse được.
- Output schema CORE 4 và CORE 8 giữ tương thích — `/evidence-qa` đọc 04, `/evidence-apply` đọc 08, không cần phân nhánh.
- Nếu user mix domain + engineering content trong cùng evidence → STOP, recommend tách 2 evidence riêng (1 domain, 1 engineering) để analyze đúng layer.
