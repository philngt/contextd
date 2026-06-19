# Concurrency Notes

Reference cho việc xử lý nhiều actor ghi/sửa cùng file shared state trong pipeline. Tóm tắt cơ chế bảo vệ thực tế + race window còn lại + operational guidance.

> Mọi atomic write + advisory lock đều qua [`scripts/lib/atomic_write.py`](../../scripts/lib/atomic_write.py). Stress test ở `scripts/test_atomic_write.py`.

---

## 1. Protected (no race left)

| File | Cơ chế | Actor(s) | Notes |
|---|---|---|---|
| `{project_dir}/.contextd/runs/{run_id}/run.json` | Advisory lock + atomic write | `emit_trace.py` hook (called by every Task completion) | Lock timeout 600ms (3×200ms). Trên timeout → log stderr `trace lost`, exit 0 (KHÔNG block pipeline). Stress: 100 concurrent writes from 4 procs = 0 lost. |
| `{project_dir}/.contextd/runs/{run_id}/{NN-stage}.json` | Atomic write (rename) | `emit_trace.py` hook | Filename per-stage là duy nhất → không cần lock. Atomic chống đọc dở. |
| `{ws}/evidence/applied/{id}/checkpoint.json` | I-8 start check + I-8.1 mid-step `session_id` check | `/evidence-apply` (single command, possibly cross-session) | Xem [evidence-lifecycle.md](evidence-lifecycle.md) §I-8/I-8.1. |
| `.contextd/context/current-task.json` | Single-writer paradigm | `contextd-context-selector` (Stage 2 of `/use-contextd`) | Builder + reviewer chỉ đọc. Pipeline strict sequential → no race. |

## 2. Tight windows — acceptable (documented, no fix needed)

| File | Window | Mitigation thực dụng |
|---|---|---|
| `{ws}/evidence/_index.md` row append/edit | Sub-second; 2 commands cùng workspace có thể overlap | V-01 sha256 dedup chặn duplicate ingest. Trường hợp khác (vd analyze + qa song song) → row khác nhau, append-only convention I-6 đủ. Nếu thấy collision thực tế → mở issue. |
| `{ws}/evidence/qa/{id}/batch-{n}-answers.md` | None thực sự — append-only I-6, sequential batch dispatch | — |
| Wiki file edits qua `contextd-curator` | None — main agent serialize delegation qua Agent tool | — |
| `{ws}/evidence/qa/{id}/todo.json` | Sub-second nếu user dùng `/evidence-qa --resume` đồng thời với chạy mới | `/evidence-qa` 1 command, ít khả năng overlap. Acceptable. |

## 3. Operational guidance

**DO:**
- Trace race protected — nếu thấy stage thiếu trong `run.json` → grep stderr log `trace lost`.
- Sử dụng `--resume` của `/evidence-apply` khi cần tiếp tục — session_id sẽ được verify mid-step (I-8.1).
- Stress test mọi shared-state thay đổi mới qua pattern của [`scripts/test_atomic_write.py`](../../scripts/test_atomic_write.py).

**DON'T:**
- KHÔNG mở 2 chat session cùng chạy `/evidence-apply` cho cùng `evid-id` → I-8/I-8.1 sẽ STOP, nhưng tốt hơn là tránh từ đầu.
- KHÔNG chạy `/evidence-{ingest,analyze}` trên cùng workspace từ 2 session khác nhau cùng lúc — `_index.md` có thể race ở window hẹp; nếu cần parallel work → ingest tới `evid-id` khác nhau.
- KHÔNG bypass `atomic_write_*` khi viết file shared state mới — thêm vào table §1 thay vì raw `Path.write_text()`.

## 4. Out of scope

- Distributed lock (Redis/etcd) — overkill cho local-only pipeline.
- Single-writer message queue — cần background daemon, không có trong Claude Code harness.
- Wiki file edit locking ở curator layer — sequential delegation đủ.

## 5. Adding a new shared file

Khi thêm 1 shared-state file vào engine:

1. Xác định actor list. Nếu > 1 actor có thể ghi cùng lúc → cần lock.
2. Dùng `with_advisory_lock` + `atomic_write_json/text` từ [`scripts/lib/atomic_write.py`](../../scripts/lib/atomic_write.py).
3. Set `timeout_ms` theo SLO của caller. Hook (5s budget) → ≤ 600ms. CLI (no SLO) → có thể lên 2000ms.
4. Trên `LockTimeout`: caller quyết định fail-loud (CLI) hay log-and-skip (hook).
5. Update bảng §1 trong doc này.

## Related

- [evidence-lifecycle.md](evidence-lifecycle.md) — I-8 (start check) + I-8.1 (mid-step session check).
- [observability.md](observability.md) — trace flow, hook setup.
- [`scripts/lib/atomic_write.py`](../../scripts/lib/atomic_write.py) — atomic write + advisory lock primitives.
- [`scripts/test_atomic_write.py`](../../scripts/test_atomic_write.py) — stress test rig.
