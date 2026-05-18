# Slash Commands — Index

Đây là slash commands cho workflow wiki-aware. Mọi command resolve **active workspace** từ `<cwd>/.claude/wiki.json` (xem [`wiki_root` Resolution Rule](../../agents/system-prompt.md) để hiểu cách path được resolve). Pipeline kiến trúc tổng thể: [agents/pipeline/README.md](../../agents/pipeline/README.md).

Quy tắc chung:
- Mỗi command có Bước 0 resolve workspace + wiki_root trước khi làm bất cứ gì.
- Mọi knowledge access scope CHỈ trong workspace active (không cross-workspace).
- Command edit wiki (contextd-update, contextd-rebase, evidence-apply) delegate qua `wiki-curator` subagent + main agent verify path sau khi curator return.

---

## Workspace setup & navigation

| Command | Purpose | When to use |
|---------|---------|-------------|
| [`/contextd-setup`](contextd-setup.md) | Tạo `.claude/wiki.json` cho codebase hiện tại; detect project name + components và pre-fill config | Lần đầu tích hợp wiki vào codebase mới, hoặc đổi workspace |
| [`/contextd-detect`](contextd-detect.md) | Validate `.claude/wiki.json` của codebase + check workspace tồn tại + scan dependency để propose update | Sanity check sau khi setup, hoặc khi `/contextd-use` lỗi resolve |
| [`/switch-workspace`](switch-workspace.md) `{name}` | Đổi `workspace` field trong `<cwd>/.claude/wiki.json` sang workspace khác | Khi cùng codebase phục vụ nhiều domain workspace, hoặc khi clone codebase nội bộ |
| [`/new-workspace`](new-workspace.md) `{name}` | Scaffold workspace mới trong `{wiki_root}/workspaces/{name}/` từ template | Khi join công ty/dự án mới, cần knowledge sandbox riêng |
| [`/list-workspaces`](list-workspaces.md) | In bảng mọi workspace + đánh dấu workspace của codebase hiện tại | Khám phá workspace nào có sẵn trước khi `/switch-workspace` |

---

## Wiki usage (per-task pipeline)

| Command | Purpose | When to use |
|---------|---------|-------------|
| [`/contextd-use`](contextd-use.md) | Chạy 5-stage pipeline (planner → context-selector → plan-reviewer → main agent code → reviewer) trước khi viết bất kỳ code wiki-aware nào | Trước MỌI task implement_feature / fix_bug / design / incident / review |
| [`/find`](find.md) `<keywords>` | Fuzzy search patterns + contracts + services + packs — top-5 với score. Skip planner ceremony | Quick lookup khi đã biết mình cần gì; trước khi mở `/contextd-use` đầy đủ |
| [`/contextd-update`](contextd-update.md) | Sync wiki với code đã thay đổi (git diff → curator áp dụng) | Sau khi code merge để wiki không drift; tự detect engine vs workspace scope |
| [`/contextd-rebase`](contextd-rebase.md) | Quét wiki vs codebase thực tế để vá mọi chỗ wiki nói khác code chạy | Định kỳ (hằng tuần/tháng) hoặc khi nghi wiki lỗi thời lớn |

---

## Codebase analysis (bootstrap wiki từ source code)

| Command | Purpose | When to use |
|---------|---------|-------------|
| [`/code-analyze`](code-analyze.md) | Snapshot metadata codebase → ingest vào evidence pipeline với `source_type=code` → sinh proposals patterns/contracts/services/ADRs để đưa vào wiki | Onboard codebase legacy; refresh platform knowledge sau major change; bootstrap workspace mới |

> Dưới capô gọi `/evidence-ingest --source code` rồi `/evidence-analyze` (CORE-CODE prompts c01–c04 + CORE 4/8). Sau đó user dùng `/evidence-qa` + `/evidence-apply` như mọi evidence khác.

---

## Reporting (wiki → tài liệu trình bày)

| Command | Purpose | When to use |
|---------|---------|-------------|
| [`/contextd-report`](contextd-report.md) | Sinh 1 file HTML self-contained tổng hợp toàn workspace (Overview / Architecture / Contracts / Patterns / Domains / ADRs / Runbooks) với citation về file nguồn | Share knowledge cho người không quen wiki; onboarding member mới; snapshot quarterly; audit gap content (`nodata` cho biết section nào thiếu) |

> Output là tài liệu trình bày — KHÔNG phải input cho code generation (đó là `/contextd-use`). Self-contained: mở browser xem ngay, không cần server/dependency.

---

## Non-tech contributors (Product / Business)

Dành cho PM, product owner, business stakeholder — đóng góp wiki mà không cần biết code. Bật [`pack-product`](../../packs/pack-product/README.md) trong workspace để có constraints + validator.

| Command | Purpose | When to use |
|---------|---------|-------------|
| [`/product-brief`](product-brief.md) `[title]` | Wizard tạo product brief mới (Problem / Target User / Success Metric / Acceptance Criteria) — chỉ hỏi business questions, không hỏi tech | PM tạo brief mới trước khi handoff engineering |
| [`/business-view`](business-view.md) `{target}` | Dịch 1 service/contract/pattern kỹ thuật sang góc nhìn business — output document persistent trong `{ws}/product/views/` | Khi cần share capability của hệ thống với PM/exec/sales/CS mà không expose jargon |
| [`/contextd-explain`](contextd-explain.md) `{topic} [--depth tldr\|short\|deep]` | On-the-fly explainer plain-language cho 1 pattern/contract/ADR/term — in console, không ghi file | Khi non-tech reader gặp 1 thuật ngữ wiki và cần hiểu nhanh trong 2 phút |

> Khác biệt: `/contextd-report` (technical, toàn workspace, HTML), `/business-view` (persistent document, 1 target, audience-cụ-thể), `/contextd-explain` (ephemeral, 1 topic, plain language).

---

## Solo builder (Non-tech expert + Claude Code)

Dành cho **chuyên gia ngành khác** (cơ khí, kế toán, y tế, luật, giáo viên, ...) tự dùng Claude Code làm assistant cá nhân để build tools hỗ trợ công việc. Họ có ý tưởng nhưng không biết tech stack nào phù hợp + chưa quen tư duy hệ thống. Bật [`pack-solo-builder`](../../packs/pack-solo-builder/README.md) trong workspace.

| Command | Purpose | When to use |
|---------|---------|-------------|
| [`/tool-design "{ý tưởng}"`](tool-design.md) | Wizard discovery (hỏi 6-8 câu) → vẽ system map → scan tool catalog → match recipe → recommend tech stack từ recipe library → ghi spec | Có ý tưởng tool mới nhưng chưa biết build thế nào |
| [`/tool-list`](tool-list.md) | In bảng toàn bộ tools trong toolbox, group theo status (building / specced / draft / done / shelved) | Xem nhanh "tôi đã build cái gì rồi" trước khi tạo tool mới (tránh trùng) |
| [`/tool-extend {slug}`](tool-extend.md) | Đề xuất update spec cho tool đã có — thêm tính năng / đổi I/O / đổi stack / refine scope. KHÔNG sinh code | Tool đã có cần thêm feature hoặc fix scope |

> **Triết lý**: spec trước, code sau. `/tool-design` chỉ ghi spec — code là session khác (user gõ "implement spec ở `{ws}/tools/{slug}-spec.md`"). Recipe library cross-platform: Linux native + Windows recommend Docker.

---

## Pipeline observability (debug + đánh giá hiệu quả wiki)

| Command | Purpose | When to use |
|---------|---------|-------------|
| [`/contextd-trace`](contextd-trace.md) `{run_id}` | Render Markdown timeline 1 run pipeline (5 stage) từ trace JSON dưới `.claude/runs/{run_id}/` | Khi output `/contextd-use` sai — debug stage nào divergence |
| [`/contextd-eval`](contextd-eval.md) | Aggregate trace nhiều run → báo cáo Markdown: hallucination rate, top knowledge gaps, plan-block rate, violation hotspots | Định kỳ review hiệu quả wiki, sau update wiki lớn, hoặc khi nghi pattern không được follow |

> Schema + design: [observability.md](../../agents/pipeline/observability.md). Manual A/B đánh giá: `{ws}/eval/golden-tasks/README.md` (per-workspace) + [task-scorecard template](../../templates/task-scorecard.md).

---

## Evidence pipeline (raw data → wiki)

Pipeline 4 bước: ingest → analyze → qa → apply. Áp dụng cho mọi `source_type` ∈ {paste, api, mcp, code}.
Reference: [agents/pipeline/evidence-lifecycle.md](../../agents/pipeline/evidence-lifecycle.md), [agents/pipeline/critical-analysis-prompts.md](../../agents/pipeline/critical-analysis-prompts.md) (text), [agents/pipeline/code-analysis-prompts.md](../../agents/pipeline/code-analysis-prompts.md) (code).

| Command | Purpose | When to use |
|---------|---------|-------------|
| [`/evidence-ingest`](evidence-ingest.md) | Pull raw data từ MCP / API / paste / code vào `{ws}/evidence/sources/{evid-id}/` (immutable sau ingest) | Khi có nguồn ngoài (Confluence, Linear, Slack, doc paste, codebase) cần đưa vào wiki |
| [`/obsidian-ingest`](obsidian-ingest.md) | Batch wrapper quanh `/evidence-ingest --source paste` cho Obsidian vault: scan folder, parse frontmatter, dedup, redaction pre-check | Khi maintain Second Brain trong Obsidian và muốn promote note đã chín sang evidence pipeline |
| [`/evidence-analyze`](evidence-analyze.md) | Chạy CORE prompts sinh `analysis/{id}/`. Text: `[01,02,04,08]`. Code: `[c01,c02,c03,c04,04,08]` | Sau ingest, để có analysis cho Q&A |
| [`/evidence-qa`](evidence-qa.md) | Q&A loop với user theo batches P0/P1/P2/P3, defer-to-expert option, sinh `verified-facts.md` khi xong | Sau analyze, để verify facts trước khi apply vào wiki |
| [`/evidence-apply`](evidence-apply.md) | Apply verified facts vào wiki docs với checkpoint/resume per-file. Router edit-vs-create theo `Affects:` path | Sau QA done; wrap `/contextd-update` hoặc `/contextd-rebase` để có manifest audit trail |

---

## Related references

- [agents/pipeline/README.md](../../agents/pipeline/README.md) — Pipeline architecture (5 stage)
- [agents/pipeline/multi-agent-pipeline.md](../../agents/pipeline/multi-agent-pipeline.md) — Subagent roles + I/O schema
- [agents/system-prompt.md](../../agents/system-prompt.md) — Engine system prompt + wiki_root resolution rule
- [workspaces/README.md](../../workspaces/README.md) — Workspace philosophy (per-codebase, no cross-workspace knowledge bleed)
