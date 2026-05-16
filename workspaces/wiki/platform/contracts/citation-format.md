# Contract: citation-format

> PAIR contract của pattern `../patterns/citation-rule.md`. Pattern describes path format skeleton; contract describes invariants + validator behavior.

## Rule

Mọi claim trong analysis output / snapshot / report PHẢI có citation. Format strict:

```
({path}:L<start>[-L<end>])           ← cite vào file thật trong repo
(raw.md#section-N)                    ← cite vào snapshot section
(raw.md#L<start>-L<end>)              ← cite vào snapshot line range
({ws}/path/to/file.md#section)        ← cite vào wiki workspace
({repo-name}/{path}:L..-L..)          ← bundle mode (repo prefix)
```

**Path rules**:
- PATH RELATIVE TO REPO ROOT (NOT absolute, NOT cwd-relative).
- Single line: `L42`. Range: `L42-L58`.
- Anchor `#section-N` cho raw.md sections; `#heading-slug` cho markdown sub-section.

## Validator behavior

| Violation | Action |
|-----------|--------|
| Claim không có citation | Re-prompt 1 lần với reminder "missing citations". Vẫn thiếu → mark `[NO-CITE]` + warn user |
| Path absolute (`/Users/...`, `D:/...`) | STOP, reject |
| Path cwd-relative (`./foo`) | STOP, reject |
| Path ngoài `code_scope` của source.yaml | STOP, reject |
| Path workspace khác `workspace_at_ingest` | STOP, reject với cross-workspace violation |

Reference: `(agents/pipeline/code-analysis-prompts.md:L519-L523)` — Cite consistency check.

## Observed evidence

- ✅ Single-repo cite: `(agents/pipeline/code-snapshot-conventions.md:L138-L155)`
- ✅ Bundle cite (repo prefix): `(agents/pipeline/code-snapshot-conventions.md:L146-L150)`
- ✅ Analysis prompt cite formats: `(agents/pipeline/code-analysis-prompts.md:L21-L24)`
- ✅ Validator implementation: `(.claude/commands/evidence-analyze.md)` — Bước 4 re-prompt logic

## Counter-examples

_(none detected — convention universal across pipeline docs)_

## Examples

✅ Correct:
- `(src/main/java/com/example/Foo.java:L42-L58)`
- `(.claude/commands/code-analyze.md:L106-L182)`
- `(raw.md#section-4)`
- `({ws}/platform/patterns/foo.md#flow)`
- `(core-framework/src/main/java/Foo.java:L42-L58)` ← bundle mode

❌ Incorrect:
- `(/Users/me/repo/foo.java:42)` ← absolute path
- `(./foo.java:42)` ← cwd-relative
- `(line 42)` ← no path
- `(foo.java)` ← no line range

## Related

- Pattern: `../patterns/citation-rule.md` (PAIR — implementation skeleton)
- Engine spec: `agents/pipeline/code-snapshot-conventions.md` Section 5
- Source: q-006, evidence `2026-05-08-engine-bootstrap-wiki-template`
