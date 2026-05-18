# Wiki Viz

HTML viewer + run browser cho wiki pipeline trace. Render `.claude/runs/{run_id}/*.json` thành HTML để debug trực quan: timeline, retrieved-vs-used diff, hallucination panel, divergence heuristic. Có watch mode cho live trace khi pipeline đang chạy.

> Companion của `/contextd-trace` (Markdown 1-run) và `/contextd-eval` (Markdown aggregate). HTML self-contained, mở local trong browser.
> Reference: [PIPELINE-VISUAL.md](../../agents/pipeline/PIPELINE-VISUAL.md), [observability.md](../../agents/pipeline/observability.md), [scripts/render_trace.py](../../scripts/render_trace.py).

---

## Input

| Arg | Required | Notes |
|---|---|---|
| `{run_id}` | optional | Run ID (vd `2026-05-08-141503-add-rest`). Prefix-match nếu duy nhất. Default → `--last`. |
| `--last` | optional | Render run mới nhất → `{run_dir}/trace.html`. |
| `--all` | optional | Render index của tất cả runs → `.claude/runs/index.html`. |
| `--watch` | optional | Live mode: poll latest run, re-render trace.html khi có file mới (dùng kèm `--last` hoặc `--run`). |
| `--out <path>` | optional | Override output path. |

---

## Bước 0 — Resolve project

Theo [workspace-resolution.md Profile C](../../agents/pipeline/workspace-resolution.md#profile-c--project-dir-only-no-workspace-lock). Set: `project_dir`, `runs_dir`, `workspace_active` (có thể null).

KHÔNG fail khi `.claude/wiki.json` thiếu — viewer best-effort mode, không filter workspace.

---

## Bước 1 — Dispatch

Gọi Python script với args đã parse. Script phong cách giống `scripts/emit_trace.py`: stdlib-only, không deps.

| User input | Bash command |
|---|---|
| `/contextd-viz` (không args) | `python {wiki_root}/scripts/render_trace.py --last --project-dir {project_dir}` |
| `/contextd-viz --last` | giống trên |
| `/contextd-viz {run_id}` | `python ... --run {run_id} --project-dir {project_dir}` |
| `/contextd-viz --all` | `python ... --all --project-dir {project_dir}` |
| `/contextd-viz --watch` | `python ... --last --watch --project-dir {project_dir}` |
| `/contextd-viz {run_id} --watch` | `python ... --run {run_id} --watch --project-dir {project_dir}` |
| `... --out path` | append `--out {path}` |

`{wiki_root}` resolve theo [system-prompt.md `wiki_root` Resolution Rule](../../agents/system-prompt.md). Tìm script tại `{wiki_root}/scripts/render_trace.py`.

Nếu không trong wiki-template (codebase khác consume wiki), command vẫn dùng absolute path script trong `{wiki_root}`.

---

## Bước 2 — Output

Script tự ghi HTML. Sau khi xong, in:

```
[OK] rendered: {path}
```

In thêm hint cho user:
- File:// link để open: `file:///{absolute_path}` (Windows: backslash → forward slash)
- Lệnh shell-native open (gợi ý, KHÔNG tự chạy):
  - Windows: `start file:///...`
  - Mac: `open file://...`
  - Linux: `xdg-open file://...`

KHÔNG tự mở browser — để user kiểm soát (tránh side-effect không mong muốn, đặc biệt trong CI/headless).

### Watch mode

`--watch` sẽ:
- In dòng status mỗi lần re-render: `[watch] re-rendered (n/5 stages, verdict=...)`
- Tự exit khi `run.json.final_verdict` không còn `INCOMPLETE`, hoặc Ctrl+C, hoặc timeout 10 phút.
- HTML có `<meta http-equiv="refresh" content="2">` → browser tự reload mỗi 2 giây.

UX khuyến nghị: mở 2 terminal — một chạy `/contextd-use "..."`, một chạy `/contextd-viz --watch`. Browser mở sẵn `trace.html`.

---

## Bước 3 — Confirm

In summary cuối:
```
[OK] rendered: {path}
   Run: {run_id}
   Stages: {n}/5
   Verdict: {final_verdict}
   Issues: {hallucination_count} halluc, {violation_count} viol
   Open: file:///{path}
```

Cho mode `--all`: in tổng số runs + path index.

---

## Hard rules

- **Read-only trên trace JSON** — script chỉ đọc, không sửa file `runs/{run_id}/*.json`. Output file mới (`trace.html`, `index.html`) ghi vào cùng thư mục với trace.
- **Workspace lock**: index HTML highlight runs có `workspace_at_run != workspace_active` thành mờ (xám), không xoá. Per-run HTML hiện banner cảnh báo nếu mismatch.
- **KHÔNG block pipeline**: viewer là on-demand, không hook tự động chạy. Pipeline (`/contextd-use`) vẫn hoạt động bình thường nếu render fail.
- **Không leak ra ngoài project_dir**: HTML output chỉ ghi vào `{project_dir}/.claude/runs/`. Không gửi metric ra external service. Mermaid load qua CDN nhưng không gửi data — fallback offline có sẵn.
- **Run_id không xuất hiện trong commit**: file `.claude/runs/` đã được khuyến cáo gitignore (xem [observability.md#L52](../../agents/pipeline/observability.md#L52)).
- **Không tự mở browser**: chỉ in `file://` link để user click/copy.

---

## Khi nào dùng

| Tình huống | Lệnh phù hợp |
|---|---|
| Vừa chạy `/contextd-use`, muốn debug 1 run | `/contextd-viz --last` |
| Muốn xem 1 run cũ | `/contextd-viz {run_id}` |
| Muốn so sánh nhiều runs theo workspace/date/verdict | `/contextd-viz --all` |
| Đang chạy `/contextd-use` ở terminal khác, muốn xem live | `/contextd-viz --watch` (terminal mới) |
| Aggregate metrics → text report | dùng `/contextd-eval` thay (Markdown, nhanh hơn) |
| Markdown timeline 1 run trong terminal | dùng `/contextd-trace --last` (không HTML) |

---

## Related

- [scripts/render_trace.py](../../scripts/render_trace.py) — Python renderer (stdlib only)
- [PIPELINE-VISUAL.md](../../agents/pipeline/PIPELINE-VISUAL.md) — Mermaid diagram giải thích pipeline
- [observability.md](../../agents/pipeline/observability.md) — schema spec
- [run-trace.schema.json](../../templates/run-trace.schema.json) — JSON schema
- [.claude/commands/contextd-trace.md](contextd-trace.md) — Markdown 1-run viewer (sister command)
- [.claude/commands/contextd-eval.md](contextd-eval.md) — Markdown aggregate (sister command)
