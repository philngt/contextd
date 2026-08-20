# pack-claude-plugin-dev — Top 10 Common Pitfalls

Anti-pattern khi build Claude Code plugin (commands/agents/skills/hooks). Additive trên [constraints.md](constraints.md).

## P01 — Thiếu plugin.json manifest
- **NG**: ship component directories nhưng thiếu `.claude-plugin/plugin.json`.
- **OK**: manifest ở đúng path với required `name`; publishable package thêm version/description/author/compatibility theo marketplace policy.
- **Why**: install fail silent; user không thấy plugin.
- **Detect**: Layer-1 `pack-claude-plugin-dev-missing-plugin-manifest`.
- **Severity**: error

## P02 — Slash command thiếu description
- **NG**: plugin-root `commands/foo.md` không có frontmatter `description`.
- **OK**: front-matter `description: "what it does"`.
- **Why**: `/help` không show; user không discover.
- **Detect**: Layer-1 — md không có `description:` frontmatter.
- **Severity**: warn

## P03 — Subagent thiếu explicit tools
- **NG**: plugin-root `agents/x.md` không liệt kê tools → inherit toàn bộ (kể cả nguy hiểm).
- **OK**: `tools: [Read, Grep]` whitelist.
- **Why**: principle of least privilege; sandbox break.
- **Detect**: Layer-1 — agent md thiếu `tools:` field.
- **Severity**: error

## P04 — Hardcoded API secret / token
- **NG**: `ANTHROPIC_API_KEY="sk-..."` trong file plugin.
- **OK**: env var; document setup; never commit.
- **Why**: secret leak khi share/publish.
- **Detect**: Layer-1 `pack-claude-plugin-dev-secret-literal` (entropy-shaped known prefixes; vẫn cần secret scanner chuyên dụng).
- **Severity**: error

## P05 — Hook chạy đồng bộ block UI
- **NG**: `UserPromptSubmit` hook gọi network 10s → user đợi.
- **OK**: hook hoàn thành trong configured timeout; long task dùng supported async/background workflow.
- **Why**: UX freeze.
- **Detect**: Layer-2 — hook code có sync HTTP / heavy compute.
- **Severity**: error

## P06 — Manifest không version
- **NG**: `plugin.json` không có `version`, hoặc giữ `0.0.1` mãi.
- **OK**: semver; bump mỗi release.
- **Why**: user không biết update; bug report không truy được.
- **Detect**: Layer-1 — manifest thiếu `version`.
- **Severity**: warn

## P07 — Command identity mơ hồ
- **NG**: docs không nêu invocation/namespace hoặc dựa vào tên có thể đổi giữa host versions.
- **OK**: test installed command identity trên minimum supported host; document exact invocation và migration alias khi rename.
- **Why**: command discovery/collision behavior thuộc host packaging contract.
- **Detect**: Layer-2 — install test + README invocation check.
- **Severity**: error

## P08 — Không document permission scope
- **NG**: plugin yêu cầu Bash + Write nhưng README không nói.
- **OK**: README có "Permissions: ...", install ask user accept.
- **Why**: trust break, install bị reject.
- **Detect**: Layer-2 — README có section Permissions.
- **Severity**: warn

## P09 — Không test path trên Windows
- **NG**: command dùng `/` slash, fail trên Windows.
- **OK**: dùng `pathlib`/`path.join`; test cross-OS.
- **Why**: bundled paths và shell assumptions dễ vỡ sau install hoặc trên OS khác.
- **Detect**: Layer-2 — CI matrix có windows-latest.
- **Severity**: warn

## P10 — Không guard against null/missing input
- **NG**: hook giả định stdin JSON luôn đủ field/đúng event.
- **OK**: parse + validate event payload; handle missing/malformed input theo event-specific failure contract.
- **Why**: silent fail, crash, bad UX.
- **Detect**: Layer-2 — hook script có input validation.
- **Severity**: warn

## Mapping to validator

| Pitfall | Layer-1 rule ID | Layer-2 self-check |
|---|---|---|
| P01 manifest | `pack-claude-plugin-dev-missing-plugin-manifest` | ✓ |
| P02 desc | `pack-claude-plugin-dev-command-missing-description` | ✓ |
| P03 tools | `pack-claude-plugin-dev-agent-missing-tools` | ✓ |
| P04 secret | `pack-claude-plugin-dev-secret-literal` | ✓ |
| P05 hook-block | — | ✓ |
| P06 version | — | ✓ |
| P07 conflict | — | ✓ |
| P08 perm-doc | — | ✓ |
| P09 windows | — | ✓ |
| P10 null-input | — | ✓ |
