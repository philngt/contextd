# pack-claude-plugin-dev — Constraints

Hard rules cho plugin Claude Code theo chuẩn Anthropic.

## Plugin Manifest

- **`.claude-plugin/plugin.json` MUST exist** khi repo ship plugin. Required fields: `name` (kebab-case), `version` (semver), `description` (≥ 20 chars), `author`.
- **`name` kebab-case** — `[a-z0-9][a-z0-9-]*`. KHÔNG underscore/CamelCase/space.
- **`version` semver strict** — `MAJOR.MINOR.PATCH`. Bump version mỗi release.
- **Description action-oriented + scope rõ** — "Tools for X" hoặc "Build/manage Y", không dùng "Helper utilities" mơ hồ.

## Slash Commands

- **File trong `.claude/commands/*.md`** với YAML frontmatter.
- **`description:` REQUIRED** — single sentence, action verb đầu, < 100 chars. Đây là dòng user thấy trong `/help`.
- **`argument-hint:` khi command nhận args** — hiển thị placeholder cho user (vd `<filename>`).
- **`allowed-tools:` để restrict** khi command có operation đặc thù (vd chỉ cho phép Read + Grep, không cho Bash).
- **Command body bằng natural language**, không phải code. Đây là prompt cho Claude, không phải script.

## Subagents

- **File trong `.claude/agents/*.md`** với frontmatter: `name`, `description`, `tools`, `model` (optional).
- **`tools:` MUST be explicit** — không để trống (inherit tất cả → security risk). Liệt kê chính xác tool subagent cần.
- **`description:` chi tiết về role + khi nào main agent nên delegate** — main agent dùng field này để routing.
- **`model:` chọn rõ ràng** — `haiku` cho task đơn giản (rẻ + nhanh), `sonnet` cho task complex, `opus` cho task nặng reasoning.

## Skills

- **File trong `.claude/skills/{name}/SKILL.md`** với frontmatter `name`, `description`.
- **`description` đủ context cho auto-invoke** — phải có "TRIGGER when:" phrase rõ điều kiện skill nên kích hoạt.
- **`description` ≥ 50 chars, ≤ 500 chars** — quá ngắn → không trigger, quá dài → noisy.
- **Skill có thể có resources** (`scripts/`, `templates/`) — reference qua relative path.

## Hooks

- **Hook config trong `settings.json#hooks`** — event types: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, `Stop`, `Notification`.
- **Hook script MUST be idempotent** — chạy lại không phá state.
- **Hook MUST be fast** (< 2s typical) — không block user experience.
- **Hook error MUST NOT crash session** — catch + log + exit 0 nếu non-critical.
- **Hook không log secrets** — sanitize input/output trước khi log.

## MCP Servers

- **`.mcp.json` ở root project** (or in plugin's `.claude-plugin/`).
- **Server entry**: `command`, `args`, `env`. KHÔNG hardcode credential — dùng env var.
- **Error handling**: server crash phải log + restart strategy. KHÔNG silent fail.
- **Tool name namespaced** — prefix server name (`{server}__{tool}`) để tránh collision.

## Security

- **Không hardcode API key / token** trong bất kỳ plugin file nào. Pattern cấm: `sk-...`, `ghp_...`, `AKIA...`, `xoxb-...`, `AIza...`.
- **Không commit `.env`, credential.json**, hoặc file chứa secret.
- **Hook + MCP server không exfiltrate** user data — chỉ truy cập đúng scope cần.

## Versioning & Distribution

- **CHANGELOG.md** cho mỗi version với breaking changes flagged.
- **README.md** với install instructions + minimum Claude Code version.
- **License rõ ràng** — `LICENSE` file ở root.
