# Critical Analysis Prompts (10) — Evidence Pipeline (source_type ∈ {paste, api, mcp})

Reference cho `/evidence-analyze`. Mỗi prompt chuyển raw data thành 1 file `analysis/{evid-id}/0X-*.md`.

**CORE (1, 2, 4, 8)** — luôn chạy bởi `/evidence-analyze`. Đủ để mở Q&A loop.
**ON-DEMAND (3, 5, 6, 7, 9, 10)** — user trigger qua `--prompt {n}` hoặc `evidence-apply` cần thêm.

> **Khi `source.yaml#source_type == "code"`** → dùng [code-analysis-prompts.md](code-analysis-prompts.md) thay vì file này. CORE 4 (`04-questions.md`) và CORE 8 (`08-knowledge-gaps.md`) DÙNG CHUNG filename ở cả hai pipeline để `/evidence-qa` và `/evidence-apply` không phân nhánh logic — input và prompt body khác nhau, output schema giống nhau.

---

## Conventions

Mỗi prompt có:
- **Inputs**: file phải đọc trước khi run.
- **Output file**: path tương đối `analysis/{evid-id}/`.
- **Output schema**: structure markdown bắt buộc (để `/evidence-qa` và `/evidence-apply` parse được).
- **Cite rule**: mọi claim phải cite — `sources/{id}/raw.normalized.md#section-N` HOẶC `sources/{id}/raw.{ext}#L<start>-L<end>` (xem fallback rule bên dưới) HOẶC `{ws}/...path` của wiki.

### Fallback khi không có `raw.normalized.md`

`raw.normalized.md` là OPTIONAL khi raw đã là markdown ngắn (xem [raw-storage-conventions.md "Khi nào cần raw.normalized.md"](raw-storage-conventions.md)).

Khi prompt input nói `raw.normalized.md (full)` mà file không tồn tại:
1. Check `sources/{id}/source.yaml#normalized` field — nếu `false` → confirm raw là markdown ngắn.
2. Đọc trực tiếp `sources/{id}/raw.{ext}` (thường `raw.md`).
3. Cite format đổi sang line number: `(raw.md#L<start>-L<end>)` thay vì `(raw.normalized.md#section-N)`.
4. KHÔNG re-normalize on-the-fly — giữ raw immutable.

Nếu `source.yaml#normalized: true` nhưng `raw.normalized.md` không tồn tại → STOP với error `EVIDENCE INTEGRITY VIOLATION: normalized=true but file missing`.

---

## CORE 1 — Resource Upload Prompt

**Output**: `01-resource-upload.md`

**Inputs**:
- `sources/{id}/raw.normalized.md` (full)
- `sources/{id}/source.yaml`

**Prompt**:
> Bây giờ có thể truy cập tài liệu tại `{path-to-raw.normalized.md}` (label: `{label}`). Hãy cung cấp:
> 1. **3 chủ đề cốt lõi** của tài liệu
> 2. Những điểm **nhất quán** / **mâu thuẫn** nội tại trong tài liệu
> 3. **Phát hiện đáng kinh ngạc nhất** (≤ 3 mục)
> 4. **Vấn đề quan trọng** mà tài liệu nêu ra nhưng chưa trả lời đầy đủ (≤ 5 mục)
>
> Mỗi mục bullet kèm citation `(raw.normalized.md#L{start}-L{end})`.

**Output schema**:
```markdown
# 01 — Resource Upload Summary

## Core themes (3)
- {theme} — `(raw.normalized.md#L..-L..)`

## Internal consistency
### Consistent
- ...
### Contradictory
- ...

## Surprising findings
- ...

## Open issues raised but unanswered
- ...
```

---

## CORE 2 — Contradiction Hunter (vs Wiki)

**Output**: `02-contradiction.md`

**Inputs**:
- `01-resource-upload.md`
- `sources/{id}/raw.normalized.md`
- `{ws}/patterns-index.md`
- `{ws}/platform/contracts/*.md`
- `{ws}/platform/patterns/*.md`
- `{ws}/projects/*/services/*.md` (chỉ services khớp `source.yaml#related_files`/`related_projects`)

**Prompt**:
> Tìm tất cả mâu thuẫn:
> (a) **giữa các tuyên bố trong tài liệu raw** với nhau
> (b) **giữa raw và wiki hiện tại của workspace `{active}`**
>
> Với mỗi mâu thuẫn:
> 1. Trích dẫn cụ thể 2 quan điểm (raw → wiki path)
> 2. Nguồn gốc mỗi bên
> 3. Bên nào **bằng chứng mạnh hơn**, vì sao
> 4. Đánh dấu `[INVESTIGATE]` nếu cần điều tra thêm

**Output schema**:
```markdown
# 02 — Contradictions

## (a) Internal contradictions
### #1 — {topic}
- Position A: "..." — `(raw.normalized.md#L..)`
- Position B: "..." — `(raw.normalized.md#L..)`
- Stronger: A | B | INVESTIGATE
- Reason: ...

## (b) Raw vs Wiki contradictions
### #1 — {topic}
- Raw says: "..." — `(raw.normalized.md#L..)`
- Wiki says: "..." — `({ws}/path/to/file.md#section)`
- Stronger: raw | wiki | INVESTIGATE
- Reason: ...
- Affected file (if raw wins): `{ws}/path/to/file.md`
```

---

## ON-DEMAND 3 — Expert Briefing Builder

**Output**: `03-expert-briefing.md`

**Inputs**: 01, 02, raw.normalized.md, optional `--persona <role>`.

**Prompt**:
> Dựa trên tài liệu, tạo bản tóm tắt chuyên nghiệp cho `{persona}` (default: "engineering lead"). Cấu trúc:
> 1. **Executive summary** — tối đa 5 câu
> 2. **Key findings** — sắp xếp theo mức quan trọng
> 3. **Strongest evidence** — kèm nguồn
> 4. **Uncertainties**
> 5. **3 recommendations** rõ ràng

---

## CORE 4 — Question Generator

**Output**: `04-questions.md`

**Inputs**: 01, 02, 08 (nếu đã có), raw.normalized.md, wiki context.

**Prompt**:
> Tạo:
> 1. **10 câu hỏi quan trọng** cần trả lời để hiểu sâu chủ đề (mark P0/P1/P2/P3 — xem `qa-batching.md`)
> 2. **5 câu hỏi tài liệu chưa trả lời đầy đủ**
> 3. **3 câu hỏi nếu trả lời khác đi sẽ thay đổi hoàn toàn cách hiểu** (counter-intuitive)
> 4. **Các câu hỏi phe phản biện có thể đặt ra**
>
> Mỗi câu hỏi format:
> ```
> - [q-XXX] (P0|P1|P2|P3) {question}
>   - reason: {why this priority}
>   - source: {01|02|08|raw|inferred}
> ```

**Output schema**:
```markdown
# 04 — Question Pool

## Block 1 — Core questions (10)
- [q-001] (P0) ... — reason: blocks_apply (contract type new) — source: 01
- [q-002] (P0) ... — reason: blocks_apply (failure handling change) — source: 02
- ...

## Block 2 — Unanswered by raw (5)
- [q-011] (P1) ...

## Block 3 — Game-changers (3)
- [q-016] (P2) ...

## Block 4 — Counter-arguments
- [q-019] (P3) ...
```

---

## ON-DEMAND 5 — Evidence Sorter

**Output**: `05-evidence-sorted.md`

**Inputs**: 01, raw.

**Prompt**:
> Với 5 tuyên bố quan trọng nhất trong tài liệu:
> 1. Đánh giá **strength** (strong | moderate | weak)
> 2. Phân loại **type**: fact (verifiable) | claim (interpretation) | opinion | unknown
> 3. Đánh dấu tuyên bố **trông chắc nhưng chứng cứ chưa đủ**
> 4. Chỉ ra phần **đáng tin cậy** vs **cần thận trọng**

---

## ON-DEMAND 6 — Timeline Reconstructor

**Output**: `06-timeline.md`

**Khi nào**: domain có yếu tố lịch sử (incident, evolution).

**Prompt**:
> Tái tạo timeline đầy đủ:
> 1. Mốc theo thứ tự thời gian
> 2. Nguyên nhân của mỗi bước ngoặt
> 3. Sự tiến hóa của consensus
> 4. So sánh với hiện tại
> 5. Xu hướng tương lai

---

## ON-DEMAND 7 — Counter-Argument Shield

**Output**: `07-counter-arguments.md`

**Inputs**: 01, 02, 03 (nếu có), 09 (nếu có).

**Prompt**:
> Chuẩn bị đối phó phản biện:
> 1. **5 lập luận phản biện mạnh nhất** nhắm vào kết luận chính
> 2. **Điểm yếu của bằng chứng** mà phê bình sẽ tấn công
> 3. **Giả định chưa được chứng minh hoàn toàn**
> 4. **Trả lời từng phản biện** dùng evidence từ tài liệu

---

## CORE 8 — Knowledge Gap Map

**Output**: `08-knowledge-gaps.md`

> **Authoritative**: file này là single source of truth cho phân loại gap `[BLOCKING]` vs `[NICE-TO-HAVE]`. `qa-batching.md` derive `blocks_apply` và `gap_severity` từ đây, KHÔNG re-classify. Khi cần đổi mức gap, re-run prompt này thay vì chỉnh tay trong qa files.

**Inputs**: 01, 02, 04, raw, wiki context.

**Prompt**:
> Xác định gaps **giữa raw + wiki hiện tại của `{active}` + bối cảnh task**:
> 1. Sub-topics quan trọng **chưa được đề cập** ở đâu
> 2. **Loại tài liệu thiếu** (config thực tế? changelog? incident postmortem?)
> 3. Kết luận nào trong raw có **bằng chứng chưa đủ**
> 4. **5 loại nguồn cần bổ sung** để evidence-set này không thể bị công kích
> 5. Mỗi gap đánh `[BLOCKING]` (block apply) hoặc `[NICE-TO-HAVE]`

**Output schema**:
```markdown
# 08 — Knowledge Gaps (vs workspace `{active}`)

## Blocking gaps (must resolve before apply)
- [BLOCKING] {gap} — affected: `{ws}/path` — needed: {what info}

## Nice-to-have gaps
- [NICE] ...

## Missing source types
- ...
```

---

## ON-DEMAND 9 — Insight Extractor

**Output**: `09-insights.md`

**Prompt**:
> Vượt xa tóm tắt:
> 1. **3 insights không hiển nhiên** mà hầu hết người đọc bỏ qua
> 2. **Patterns xuyên suốt** tài liệu nhưng không nêu rõ
> 3. Điều **tác giả ngụ ý** nhưng chưa nói trực tiếp
> 4. Data points **trông nhỏ nhưng quan trọng**

---

## ON-DEMAND 10 — Final Report Generator

**Output**: `10-final-report.md`

**Inputs**: tất cả analysis files đã có + `qa/{id}/verified-facts.md` (nếu Q&A đã xong).

**Khi nào**: trước stakeholder presentation HOẶC `/evidence-apply --mode update --with-report`.

**Prompt**:
> Tạo báo cáo nghiên cứu hoàn chỉnh về `{label}`:
> 1. Title + executive summary
> 2. Key findings + bằng chứng
> 3. Phân tích vượt sự kiện
> 4. Hạn chế + uncertainties
> 5. Conclusion + next steps
>
> Tone: `{academic | professional | conversational}` (default: professional).

---

## Run order

1. `/evidence-analyze --id <id>` → CORE 1, 2, 4, 8 (luôn).
2. User chạy `/evidence-qa` → P0+P1 batches.
3. User trigger ON-DEMAND nếu cần (vd `--prompt 06` cho timeline).
4. `/evidence-apply` → optional auto-trigger CORE 10 nếu user pass `--with-report`.
