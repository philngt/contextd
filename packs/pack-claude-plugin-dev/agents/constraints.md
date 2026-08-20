# pack-claude-plugin-dev — Constraints

Hard rules cho plugin Claude Code theo chuẩn Anthropic.

## Plugin Manifest (`pack-claude-plugin-dev-plugin-manifest`)

- **`.claude-plugin/plugin.json` MUST exist** khi repo ship plugin. Host-required baseline is `name`; publishable plugins also carry version, description, author, compatibility and license metadata per marketplace policy.
- **`name` kebab-case** — `[a-z0-9][a-z0-9-]*`. KHÔNG underscore/CamelCase/space.
- **`version` semver strict** — `MAJOR.MINOR.PATCH`. Bump version mỗi release.
- **Description action-oriented + scope rõ** — "Tools for X" hoặc "Build/manage Y", không dùng "Helper utilities" mơ hồ.

## Slash Commands (`pack-claude-plugin-dev-commands`)

- **File trong plugin-root `commands/*.md`** với YAML frontmatter; không đặt dưới project-local `.claude/commands/` khi đóng gói plugin.
- **`description:` REQUIRED** — concise, specific, nêu behavior/usage để discovery và `/help` có signal tốt.
- **`argument-hint:` khi command nhận args** — hiển thị placeholder cho user (vd `<filename>`).
- **`allowed-tools:` để restrict** khi command có operation đặc thù (vd chỉ cho phép Read + Grep, không cho Bash).
- **Command body bằng natural language**, không phải code. Đây là prompt cho Claude, không phải script.

## Subagents (`pack-claude-plugin-dev-agents`)

- **File trong plugin-root `agents/*.md`** với frontmatter: `name`, `description`, `tools`; `model` là optional và phải dùng giá trị được host/version đang pin hỗ trợ.
- **`tools:` MUST be explicit** — không để trống (inherit tất cả → security risk). Liệt kê chính xác tool subagent cần.
- **`description:` chi tiết về role + khi nào main agent nên delegate** — main agent dùng field này để routing.
- **Không hardcode model-selection folklore** — default/inherit hoặc model alias từ compatibility policy; benchmark/eval trước khi override.

## Skills (`pack-claude-plugin-dev-skills`)

- **File trong plugin-root `skills/{name}/SKILL.md`** với frontmatter `name`, `description`.
- **`description` đủ context cho discovery** — nêu capability + when-to-use và, khi dễ nhầm, when-not-to-use; không bắt buộc một magic phrase hay length tùy ý.
- **Skill có thể có resources** (`scripts/`, `templates/`) — reference qua relative path.

## Hooks (`pack-claude-plugin-dev-hooks`)

- **Hook config trong plugin-root `hooks/hooks.json`**; event name/payload/response phải khớp Claude Code version được pin.
- **Hook script MUST be idempotent** — chạy lại không phá state.
- **Hook MUST respect configured timeout** — synchronous work tối thiểu; long-running work phải dùng supported async/background pattern.
- **Hook failure semantics explicit** — catch/log và trả exit/JSON behavior đúng event contract; không blanket `exit 0` nếu hook là enforcement gate.
- **Hook không log secrets** — sanitize input/output trước khi log.

## MCP Servers (`pack-claude-plugin-dev-mcp-servers`)

- **`.mcp.json` ở plugin root**; bundled command/path dùng `${CLAUDE_PLUGIN_ROOT}`. Không đặt component config tùy ý trong `.claude-plugin/` trừ manifest/marketplace metadata.
- **Server entry**: `command`, `args`, `env`. KHÔNG hardcode credential — dùng env var.
- **Error handling**: server crash phải log + restart strategy. KHÔNG silent fail.
- **Tool name namespaced** — prefix server name (`{server}__{tool}`) để tránh collision.

## Security (`pack-claude-plugin-dev-security`)

- **Không hardcode API key / token** trong bất kỳ plugin file nào. Pattern cấm: `sk-...`, `ghp_...`, `AKIA...`, `xoxb-...`, `AIza...`.
- **Không commit `.env`, credential.json**, hoặc file chứa secret.
- **Hook + MCP server không exfiltrate** user data — chỉ truy cập đúng scope cần.

## Versioning & Distribution (`pack-claude-plugin-dev-distribution`)

- **CHANGELOG.md** cho mỗi version với breaking changes flagged.
- **README.md** với install instructions + minimum Claude Code version.
- **License rõ ràng** — `LICENSE` file ở root.

> Anti-patterns lặp lại trong domain này: xem [common-pitfalls.md](common-pitfalls.md) (Top 10 với rule/why/detect/severity).
