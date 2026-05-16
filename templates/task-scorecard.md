# Task Scorecard — A/B Wiki Effectiveness

> Manual rubric. Chấm cả 2 lần chạy (A = wiki-on, B = wiki-off) trên cùng 1 golden task. Delta `score_A − score_B` phản ánh đóng góp của wiki.

---

## Metadata

| Field | Value |
|-------|-------|
| Task ID | {ví dụ `gt-01-add-rest-endpoint`} |
| Workspace | {ws} |
| Run A — wiki-on | {run_id_A} |
| Run B — wiki-off | {run_id_B} |
| Date scored | {YYYY-MM-DD} |
| Scorer | {tên user} |

---

## Rubric (10 tiêu chí, mỗi tiêu chí 0-3 điểm)

> Quy ước: **0** = không đạt, **1** = đạt một phần, **2** = đạt phần lớn, **3** = đạt đủ và đúng.
> Khi B "không có wiki để dùng", chấm theo output thực tế — nếu agent đoán đúng, vẫn cho điểm.

| # | Tiêu chí | Mô tả | A | B |
|---|----------|-------|---|---|
| 1 | Pattern adoption | Output có dùng đúng pattern theo expected.md không? | _ | _ |
| 2 | Contract adherence | Topic/URL/schema khớp contract không (hoặc nếu không có wiki, có conform với best practice của workspace không)? | _ | _ |
| 3 | No hallucination | Không reference pattern/file/contract không tồn tại | _ | _ |
| 4 | Domain rules | State transitions, business rules không bị vi phạm | _ | _ |
| 5 | Failure handling | Retry + DLQ + edge cases được handle (không chỉ happy path) | _ | _ |
| 6 | Config externalization | Không hardcode topic, batch size, timeout, region | _ | _ |
| 7 | Project overrides | Tôn trọng Config Overrides của project (nếu có) | _ | _ |
| 8 | Code quality | Constructor injection, naming, layout đúng convention | _ | _ |
| 9 | Completeness | Implementation đủ scope task, không nửa vời | _ | _ |
| 10 | Citation | Mỗi quyết định kỹ thuật trỏ về 1 entry trong context (chỉ áp dụng cho A; B chấm theo `## Assumptions` rõ ràng) | _ | _ |

---

## Auto-fields (đọc từ trace)

| Metric | A | B |
|--------|---|---|
| `01-planner.unverified_count` | _ | _ |
| `02-context.gap_count` | _ | _ |
| `03-plan-review.verdict` | _ | _ |
| `04-builder.assumptions_count` | _ | _ |
| `05-review.violation_count` | _ | _ |
| `05-review.hallucination_count` | _ | _ |

---

## Score

| Run | Sum (max 30) | Notes |
|-----|--------------|-------|
| A — wiki-on | _ | _ |
| B — wiki-off | _ | _ |
| **Δ (A − B)** | _ | Wiki contribution |

**Interpretation:**
- Δ ≥ 8: wiki đóng góp lớn cho task này.
- 3 ≤ Δ < 8: wiki có ích, nhưng B gần đạt → có thể thêm pattern/contract để rộng khoảng cách.
- 0 ≤ Δ < 3: wiki không thật sự dùng đến (task quá đơn giản, hoặc wiki không cover đúng).
- Δ < 0: wiki *làm tệ hơn* — agent bị nhiễu bởi context không liên quan. Cần review.

---

## Action items (sau scoring)

- [ ] Gap nào trong A xuất hiện cũng trong top-3 `/wiki-eval` Top Gaps? → Ưu tiên `/evidence-ingest`.
- [ ] Pattern nào dùng được mà builder bỏ qua? → Bổ sung vào `patterns-index.md` với "When to use" rõ hơn.
- [ ] Contract nào bị vi phạm trong B mà A pass? → Quote contract trong service docs.
- [ ] Nếu Δ < 3 lặp lại nhiều task → review structure wiki, có thể context-filter.md ranking sai.

---

## Lưu kết quả

Lưu file đã chấm vào `{ws}/eval/results/{YYYY-MM-DD}-{task-id}.md` (per-workspace). KHÔNG commit nếu chứa data nội bộ — `.gitignore` đã cover `workspaces/*/eval/results/*`.
