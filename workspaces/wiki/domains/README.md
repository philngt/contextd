# Domain workflows — business rules & state machines

Mỗi domain con (vd `surgery/`, `billing/`, `ticket/`) chứa: workflow states, transition rules, business invariants. Khác `platform/` (technical) — đây là **business logic** không phụ thuộc stack.

Ví dụ tạo domain đầu tiên: `mkdir domains/{domain-name}` rồi tạo `domains/{domain-name}/workflow.md` với state machine + transitions.

Xoá README này khi đã có domain thực.
