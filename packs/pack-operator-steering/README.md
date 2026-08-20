# pack-operator-steering

Agent-operator steering pack for recovering direction, retaining human decision
ownership, auditing context/drift, planning remediation, and preserving durable
decisions and handoffs.

## When to enable

Workspace opts in by adding `- pack-operator-steering` under `## Packs` in `workspaces/{ws}/workspace.md`.

Enable when the workspace needs:
- Operators to inspect whether an agent has enough context before work continues.
- Người dùng không biết nên làm gì tiếp, cần tiếp tục, tạm dừng, chuyển hướng hay dừng hẳn.
- Một chuỗi vibe-coding đang để AI tự chọn mục tiêu hoặc roadmap mà không có operator decision rõ ràng.
- Drift checks against decisions, assumptions, risks, and accepted defaults.
- Remediation plans that name root cause, owner, acceptance criteria, and verification method.
- Durable handoff briefs for long-running agent work.

## What it adds

- **Canonical knowledge** (`knowledge.md`) - principles plus component-scoped
  mental models, standards, failure signals, evidence, and stop conditions.
- **Templates** (`templates/`) - context audit, drift report, remediation plan, decision note, handoff brief, and workflow mental model.
- **Wayfinding checkpoint** - khôi phục current orientation, phân loại gap, dựng decision frontier và chốt `continue|pause|pivot|stop`.
- **Manifest routing** (`pack.yaml#retrieval`) - component-to-workspace-doc mapping.
- **Static rules** (`scripts/rules.py`) - narrow checks whose IDs are documented
  in canonical knowledge.

This is the first manifest-v3 pack. Files under `agents/` remain readable v2
compatibility adapters during migration, but runtime v3 does not load them as a
second guidance plane.

## Components declared

- `context-audit`
- `drift-check`
- `remediation-planning`
- `decision-ledger`
- `handoff-quality`
- `workflow-mental-model`
- `operator-wayfinding`

## Wayfinding and human agency

Wayfinding không bắt AI quyết định thay user và cũng không biến mọi task thành
một cuộc phỏng vấn dài. Khi component này được trigger, flow mặc định là:

```text
orient → inspect facts → classify gap → expose decision frontier
       → recover decision-ready knowledge → recommend one bounded next step
       → continue/pause/pivot/stop
```

- Fact tìm được từ repo/runtime là việc của agent; không hỏi lại user.
- Material decision vẫn thuộc user. Agent phải đưa recommended answer, lý do và
  impact nếu sai thay vì trả ngược một câu hỏi trống.
- Mặc định hỏi một material decision mỗi lượt. Chỉ batch các câu độc lập khi
  user muốn.
- `Tôi chưa biết` là input hợp lệ: route sang evidence/knowledge gap hoặc một
  research step nhỏ, không tự biến thành approval.
- Knowledge recovery tách rõ: điều user phải hiểu để steer, implementation detail
  có thể giao AI, và phần cần evidence/expert. Không dump một tutorial dài.
- Trong một explicit wayfinding session, không triển khai hướng material mới
  trước khi user xác nhận đã đủ shared understanding hoặc chủ động thoát session.

Pattern này tham khảo [`grill-me`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md)
và reusable [`grilling`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md):
map decision dependencies, tự tìm facts, đưa recommendation và giữ quyết định ở
phía user. contextd bổ sung evidence labels, stage orientation, lifecycle memory
và stop taxonomy; pack không phụ thuộc runtime của skill nguồn.

## How to invoke

Sau khi bật pack, user không cần nhớ tên component. Có thể nói trực tiếp:

```text
Tôi đã vibe code khá lâu và đang bị lạc hướng. Hãy kiểm tra repo/context hiện tại,
cho tôi biết đang ở stage nào, gap chính là gì, điều tối thiểu tôi cần hiểu,
một quyết định cần chốt tiếp theo, recommendation của bạn, và nên continue,
pause, pivot hay stop. Đừng implement
hướng mới trước khi tôi xác nhận.
```

Nếu đã biết project/task, thêm tên cụ thể để retrieval lấy đúng knowledge map và
decisions. `contextd context "<prompt>" --preview` cho phép kiểm tra template và
evidence nào sẽ được load trước khi trao quyền cho agent.

## Conflicts with

(none)

## Notes

This pack borrows practical patterns from operator-facing steering workflows,
but it has no runtime dependency on WOAFC, `grill-me`, or any
`.woafc/project/` store. `contextd` remains the build substrate; the pack adds
deterministic docs, templates, retrieval rules, and validation hints.

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)

## When not to enable

- Task nhỏ, rõ outcome/next action/stop condition và không có decision history, handoff hoặc nguy cơ drift.
- Cần coding rules của một stack; pack này chẩn đoán/steer chứ không thay thế domain pack.
- Cần hỗ trợ sức khỏe tinh thần/cá nhân hoặc clinical guidance; pack chỉ steer project/workflow decisions.

## Retrieval behavior

Wayfinding, audit, drift, remediation, decision, handoff và mental model route độc
lập. Wayfinding ưu tiên current project map, decisions, evidence và runbook trước
khi hỏi user; các component khác không bị kéo vào chỉ vì pack đang active.
Runtime luôn load compact manifest metadata + `knowledge.md#Global Principles`,
sau đó chỉ load section `## Component: ...` được keyword routing chọn.

## Verification

```bash
contextd pack-validate --pack pack-operator-steering --format text
contextd context "Audit context drift before handoff" --preview --format json
contextd context "I am lost; what should I do next and should I stop?" --preview --format json
python scripts/validate.py --file <handoff-fixture> --workspace <workspace-with-pack>
```
