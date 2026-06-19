# Repetition Detection (UserPromptSubmit hook)

## Mục tiêu

User trong hệ contextd thường **lặp đi lặp lại** các yêu cầu (gõ cùng kiểu prompt, gọi cùng workflow ad-hoc) trước khi chính thức chuẩn hoá thành **skill / slash command / subagent / pack**. Mỗi lần lặp:

- tốn context (assistant phải re-discover cùng knowledge);
- dễ drift khỏi convention vì không có guard rails;
- chôn vùi cơ hội tự động hoá.

Hook `scripts/detect_repetition.py` (gắn vào event `UserPromptSubmit`) quan sát prompt, gom thành cluster, và khi đủ ngưỡng thì **inject hint** vào `additionalContext` để assistant nhắc user promote pattern thành artifact lâu dài qua [`/suggest-automation`](../../.claude/commands/suggest-automation.md).

## Decisions đã chốt

| Quyết định | Giá trị |
|-----------|---------|
| Trigger | `UserPromptSubmit` (1 hook duy nhất) |
| Scope | **Per-workspace** — log dưới `{ws}/.observations/`, KHÔNG cross-workspace |
| Output kênh | `hookSpecificOutput.additionalContext` (string ≤ 400 chars) |
| Authoring | Assistant interactive qua `/suggest-automation`; KHÔNG auto-generate file |
| Storage | JSON + JSONL local, không service ngoài |
| Latency budget | < 800 ms self-imposed; harness timeout 2 s |
| Failure mode | Mọi lỗi → exit 0, log stderr; KHÔNG bao giờ chặn turn |

## Data model

```
workspaces/{ws}/.observations/
├── prompts.jsonl       # append-only, 1 dòng / prompt
├── clusters.json       # cluster state (rolling)
├── suppressions.json   # user dismiss / đã resolve thành artifact
└── clusters.json.lock  # advisory lock (atomic_write)
```

### `prompts.jsonl` — observation log

```jsonl
{"ts":"2026-05-15T08:42:11+00:00","prompt_hash":"a1b2...","tokens":["rebase","wiki","merge"],"prompt_preview":"rebase wiki sau khi merge","cwd":"d:/repo"}
```

- `prompt_hash`: SHA-256 truncate 16 char của raw prompt.
- `tokens`: capped 40 tokens (đã normalize).
- `prompt_preview`: first 120 chars của raw prompt — đủ context khi user review qua `/observations-clear --list`, KHÔNG dài đến mức log secret toàn bộ.

> **Privacy**: chỉ first 120 chars + token list. `.gitignore` thêm `prompts.jsonl` để raw không lên git. Retention sẽ thực hiện ở Phase B (auto-trim quá 30 ngày).

### `clusters.json` — cluster state

```json
{
  "stage": "observations",
  "updated_at": "2026-05-15T08:42:11+00:00",
  "clusters": [
    {
      "id": "rebase-contextd-merge-a1b2c3",
      "representative_tokens": ["rebase","wiki","merge","code","review"],
      "count": 7,
      "first_seen": "2026-04-10T...",
      "last_seen": "2026-05-14T...",
      "last_hinted_at": "2026-05-12T...",
      "members": ["h1","h2","..."]
    }
  ]
}
```

- `id`: top-3 normalized tokens + 6-char hash of token set → stable + human-readable.
- `representative_tokens`: union các token đã thấy, cap 20.
- `members`: rolling tail 50 prompt_hash mới nhất (để gắn observation ↔ cluster khi debug).

### `suppressions.json`

```json
{
  "dismissed": ["rebase-contextd-merge-a1b2c3"],
  "resolved": [
    { "cluster_id": "...", "artifact": "workspaces/c7/.claude/commands/rebase-contextd.md", "ts": "..." }
  ]
}
```

- `dismissed`: user chủ động ẩn qua `/observations-clear --dismiss`.
- `resolved`: cluster đã được promote thành artifact qua `/suggest-automation`.

## Algorithm

```
INPUT: prompt (str), cwd (Path)

1. resolve workspace từ <cwd>/.contextd/config.json (rule "knowledge_root Resolution"
   trong agents/system-prompt.md). Nếu thiếu → exit 0 silent.

2. tokens = normalize(prompt)
   - lowercase, regex [a-z0-9À-ỹà-ỹ_]+
   - drop stopwords (EN + VI, ~140 từ)
   - drop tokens len < 2
   if len(tokens) < MIN_PROMPT_TOKENS (3): exit 0.

3. Append observation vào prompts.jsonl (best-effort).

4. Acquire advisory lock trên clusters.json (timeout 400ms).
   - Load clusters, prune những cluster last_seen > window_days.
   - assign_to_cluster:
       best = argmax_cluster jaccard(tokens, c.representative_tokens)
       if best_score >= REP_JACCARD (0.6): bump count, union tokens
       else: spawn new cluster
   - Load suppressions.

5. should_hint(cluster):
   - cluster.count >= REP_MIN_COUNT (3)
   - cluster.id NOT IN suppressions.dismissed
   - now - last_hinted_at >= REP_COOLDOWN_HOURS (6)

6. Nếu should_hint:
   - load_artifact_keywords(knowledge_root, workspace):
       scan front-matter (name + description) của:
         .claude/commands/*.md
         .claude/agents/*.md
         packs/*/agents/*.md
         packs/*/.claude/commands/*.md
         packs/*/skills/*.md
         workspaces/{ws}/agents/*.md
         workspaces/{ws}/.claude/commands/*.md
   - covered_by = best artifact với jaccard(cluster_rep, artifact_kw) >= 0.5
   - Nếu KHÔNG có covered_by:
       cluster.last_hinted_at = now
       emit hint
   - Nếu CÓ covered_by: stay silent (artifact đã giải quyết intent này)
     KHÔNG bump last_hinted_at → nếu user vẫn lặp dù đã có artifact,
     đó là signal artifact đang miss-fire (handle ở /suggest-automation refine path)

7. atomic_write_json(clusters.json, ...)
8. Release lock, exit 0.
```

### Tunables (env var)

| Var | Default | Ý nghĩa |
|-----|---------|---------|
| `REP_JACCARD` | 0.6 | Ngưỡng merge prompt vào cluster |
| `REP_MIN_COUNT` | 3 | Tối thiểu prompt mới sinh hint |
| `REP_WINDOW_DAYS` | 14 | Cluster già hơn → prune |
| `REP_COOLDOWN_HOURS` | 6 | Min giữa 2 lần hint cùng 1 cluster |
| `REP_HISTORY` | 200 | (Reserved) max observation đọc trở lại |
| `REP_COVERAGE_JACCARD` | 0.5 | Ngưỡng để coi cluster đã được artifact cover |

## Hint format

```
[repetition-detector] Pattern lap phat hien: cluster='{id}', {N} lan trong
khoang {first}..{last}. Theme: '{top 5 tokens}'. Chua co skill/command/agent
bao phu. Goi y user chay /suggest-automation {id} de chuyen thanh
skill | slash command | subagent | pack, hoac /observations-clear --dismiss {id}
neu khong muon nhac lai.
```

ASCII-only intentionally — hint hiển thị trong nhiều terminal khác nhau.

## Quan hệ với các hook khác

| Hook | File | Trigger | Mục đích | Chia sẻ gì? |
|------|------|---------|----------|-------------|
| `emit_trace.py` | `scripts/emit_trace.py` | PostToolUse (matcher=Task) | Ghi trace pipeline contextd subagent | KHÔNG — file riêng `.contextd/runs/` |
| `detect_repetition.py` | `scripts/detect_repetition.py` | UserPromptSubmit | Detect lặp + suggest automation | KHÔNG |

Hai hook độc lập về state. Phase B sẽ add `log_invocation.py` (usage telemetry cho lifecycle) — cũng độc lập.

## Privacy & security

- **Prompt chứa secret**: chỉ store first 120 chars + tokens + hash. Raw prompt KHÔNG được lưu nguyên.
- **`.gitignore`**: `workspaces/*/.observations/prompts.jsonl` — observation log không lên git.
- **`clusters.json` + `suppressions.json`** CÓ thể commit (chỉ chứa token + id) nếu team muốn share automation backlog.
- **Cross-workspace leak**: detector strict đọc/ghi trong `workspaces/{active_ws}/.observations/`. Test `test_e2e_missing_wiki_json_silent` xác nhận hook không tự ý ghi khi không resolve được workspace.

## Failure modes & mitigations

| Mode | Mitigation |
|------|------------|
| `.contextd/config.json` thiếu | silent exit 0, không output |
| `clusters.json` corrupt | warn stderr, treat as empty, đè bằng atomic write mới |
| Lock contention (2 prompt cùng giây) | timeout 400 ms → skip update, observation vẫn ghi |
| Hook chạy chậm | self-budget 800 ms; harness timeout 2 s |
| False positive (3 prompt khác hẳn nhưng cùng vài keyword) | cooldown 6h + dismiss list |
| Artifact đã có nhưng vẫn lặp | KHÔNG bump `last_hinted_at` → assistant có thể đề xuất refine path qua `/suggest-automation` |

## Roadmap

### Phase A (P0 — đang triển khai)
- ✅ Detect & hint
- ✅ `/suggest-automation`, `/observations-clear`
- ✅ Unit + e2e tests

### Phase B (P1 — lifecycle layer)
- `templates/automation-artifact.md`: front-matter chuẩn (status, created_at, review_after, related_patterns/contracts).
- `scripts/log_invocation.py`: hook ghi `usage.jsonl`.
- `/review-automations`: report keep/refine/deprecate/retire/merge.
- `/eval-automation <name>`: deep-dive 1 artifact, replay golden tasks nếu có.
- `scripts/lint-automations.py`: CI-grade anti-rot validator.

Detail trong [plan gốc](C:\Users\APC\.claude\plans\c-n-1-c-i-hook-buzzing-rainbow.md).
