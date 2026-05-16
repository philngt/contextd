#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scaffold-pack.py - Create skeleton for a new pack.

Usage:
    python scripts/scaffold-pack.py <pack-name>
    python scripts/scaffold-pack.py pack-mobile-flutter

Creates:
    packs/{name}/
    ├── README.md                          (stub)
    ├── pack.yaml                          (from templates/pack.yaml + name pre-filled)
    ├── agents/
    │   ├── constraints.md                 (stub)
    │   ├── coding-rules.md                (stub)
    │   └── pipeline/
    │       ├── prompt-overrides.md        (stub)
    │       ├── retrieval-map.md           (stub)
    │       └── validator-rules.md         (stub)
    └── scripts/
        └── rules.py                       (boilerplate with _vio() helper, empty RULES list)

Convention: pack name MUST be `pack-{slug}` (kebab-case). Script enforces.

After scaffolding, customize ~3 files:
    1. packs/{name}/pack.yaml  - fill components + keywords + conflicts_with
    2. packs/{name}/agents/constraints.md  - hard rules specific to stack
    3. packs/{name}/scripts/rules.py  - add validator functions to RULES list
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = REPO_ROOT / "packs"
TEMPLATE_PACK_YAML = REPO_ROOT / "templates" / "pack.yaml"

NAME_RE = re.compile(r"^pack-[a-z0-9][a-z0-9-]*$")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        die("Usage: python scripts/scaffold-pack.py <pack-name>")

    name = sys.argv[1].strip()
    if not NAME_RE.match(name):
        die(f"Invalid pack name '{name}'. Must match `pack-[a-z0-9][a-z0-9-]*` "
            "(kebab-case, prefix `pack-`).")

    pack_dir = PACKS_DIR / name
    if pack_dir.exists():
        die(f"Pack already exists: {pack_dir.relative_to(REPO_ROOT)}")
    if not TEMPLATE_PACK_YAML.exists():
        die(f"Template missing: {TEMPLATE_PACK_YAML.relative_to(REPO_ROOT)}")

    short = name.removeprefix("pack-")

    # 1. Create directory tree
    (pack_dir / "agents" / "pipeline").mkdir(parents=True)
    (pack_dir / "scripts").mkdir()

    # 2. pack.yaml - load template, swap name placeholder
    pack_yaml_text = TEMPLATE_PACK_YAML.read_text(encoding="utf-8")
    pack_yaml_text = pack_yaml_text.replace("pack-{your-name}", name)
    (pack_dir / "pack.yaml").write_text(pack_yaml_text, encoding="utf-8")

    # 3. README.md
    (pack_dir / "README.md").write_text(
        f"""# {name}

{{One-line description of the stack/use case this pack serves.}}

## When to enable

Workspace opts in by adding `- {name}` under `## Packs` in `workspaces/{{ws}}/workspace.md`.

Enable when the workspace stack includes:
- {{condition 1}}
- {{condition 2}}

## What it adds

- **Constraints** ({name}/agents/constraints.md) - hard rules for this stack
- **Coding rules** ({name}/agents/coding-rules.md) - idioms + preferred patterns
- **Validator rules** ({name}/agents/pipeline/validator-rules.md + scripts/rules.py) - automated gates
- **Retrieval map** ({name}/agents/pipeline/retrieval-map.md) - `component → wiki docs` mapping
- **Prompt overrides** ({name}/agents/pipeline/prompt-overrides.md) - pack-specific prompt injects

## Components declared

See `pack.yaml#components`.

## Conflicts with

(none) - list pack names here if this pack cannot coexist.

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)
""",
        encoding="utf-8",
    )

    # 4. agents/constraints.md
    (pack_dir / "agents" / "constraints.md").write_text(
        f"""# {name} - Constraints

Hard rules đặc thù cho stack/use case của pack này. Additive trên engine constraints. Strict-only direction.

## {{Category 1}}

- **{{Rule statement}}** - {{Why + example}}.
- **{{Rule statement}}** - {{Why + example}}.

## {{Category 2}}

- **{{Rule statement}}** - {{Why + example}}.

## Related

- Engine baseline: [`agents/constraints.md`](../../../agents/constraints.md)
- Pack validator rules: [pipeline/validator-rules.md](pipeline/validator-rules.md)
- Pack coding rules: [coding-rules.md](coding-rules.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../../agents/cross-cutting-principles.md)
""",
        encoding="utf-8",
    )

    # 5. agents/coding-rules.md
    (pack_dir / "agents" / "coding-rules.md").write_text(
        f"""# {name} - Coding Rules

Idioms + preferred patterns. Less strict than constraints - these are conventions, không phải gates.

## {{Category 1}}

- {{Convention}}.

## {{Category 2}}

- {{Convention}}.
""",
        encoding="utf-8",
    )

    # 6. agents/pipeline/prompt-overrides.md
    (pack_dir / "agents" / "pipeline" / "prompt-overrides.md").write_text(
        f"""# {name} - Prompt Overrides

Pack-specific additions to the system prompt + builder prompt. Injected by pipeline when this pack is active in the workspace.

## System prompt addition

{{Text injected after engine baseline system prompt. Keep concise.}}

## Builder prompt self-check (additions)

- {{Self-check item specific to this stack}}
- {{Self-check item specific to this stack}}
""",
        encoding="utf-8",
    )

    # 7. agents/pipeline/retrieval-map.md
    (pack_dir / "agents" / "pipeline" / "retrieval-map.md").write_text(
        f"""# {name} - Retrieval Map

Component → wiki doc mapping for this pack. Merged into engine retrieval map by pipeline (see [task-to-docs-map.md](../../../../agents/pipeline/task-to-docs-map.md)).

| Component | Docs to retrieve |
|-----------|------------------|
| `{{component-1}}` | `{{ws}}/platform/patterns/{{name}}.md` |
| `{{component-2}}` | `{{ws}}/platform/contracts/{{name}}.md` |

Components must match `pack.yaml#components`. Pipeline fail-fast nếu mismatch.
""",
        encoding="utf-8",
    )

    # 8. agents/pipeline/validator-rules.md
    (pack_dir / "agents" / "pipeline" / "validator-rules.md").write_text(
        f"""# {name} - Validator Rules

Layer 1 (static) validator rules. Implemented in `scripts/rules.py` - this doc is the human-readable catalog.

Rule IDs MUST be prefixed `{name}-`.

## Catalog

| Rule ID | Severity | Triggers on | Detects |
|---------|----------|-------------|---------|
| `{name}-{{rule-1}}` | error | `*.{{ext}}` files matching `{{pattern}}` | {{What it catches + why bad}} |
| `{name}-{{rule-2}}` | warn | ... | ... |

## Related

- Implementation: [`scripts/rules.py`](../../scripts/rules.py)
- Engine validator pipeline: [`agents/pipeline/validator-rules.md`](../../../../agents/pipeline/validator-rules.md)
""",
        encoding="utf-8",
    )

    # 9. scripts/rules.py - boilerplate with _vio() + empty RULES
    (pack_dir / "scripts" / "rules.py").write_text(
        f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} - Layer 1 validator rules.

Loaded dynamically by `scripts/validate.py` via `scripts/pack_loader.py` when
the active workspace opts into this pack (in workspace.md `## Packs` section).

Each rule is a function:
    rule_<id>(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]

Rules are exposed via the module-level `RULES` list, which `pack_loader.py`
imports and appends to the global `ALL_RULES`.

Rule IDs: prefixed `{name}-`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List


def _vio(rule: str, severity: str, file_path: Path, lineno: int,
         snippet: str, message: str) -> Dict:
    return {{
        "rule": rule,
        "severity": severity,
        "file": file_path.as_posix(),
        "line": lineno,
        "snippet": snippet.strip()[:200],
        "message": message,
    }}


def _strip_line_comment(line: str) -> str:
    """Strip // or # line comments (adjust per language target)."""
    for marker in ("//", "#"):
        idx = line.find(marker)
        if idx >= 0:
            return line[:idx]
    return line


# ---------------------------------------------------------------------------
# Rules - add functions here, then append to RULES list at the bottom.
# ---------------------------------------------------------------------------

# def rule_{short}_example(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]:
#     out = []
#     for i, raw in enumerate(lines, start=1):
#         line = _strip_line_comment(raw)
#         # ... detect violation ...
#         # out.append(_vio(
#         #     "{name}-example", "error", file_path, i, raw,
#         #     "Description of what is wrong + how to fix."
#         # ))
#     return out


# Module-level export for pack_loader
RULES: List = [
    # rule_{short}_example,
]
''',
        encoding="utf-8",
    )

    # 10. Confirm
    print(f"[OK] Pack scaffolded: {pack_dir.relative_to(REPO_ROOT)}")
    print()
    print("Files created:")
    for rel in [
        "README.md",
        "pack.yaml",
        "agents/constraints.md",
        "agents/coding-rules.md",
        "agents/pipeline/prompt-overrides.md",
        "agents/pipeline/retrieval-map.md",
        "agents/pipeline/validator-rules.md",
        "scripts/rules.py",
    ]:
        print(f"  {pack_dir.relative_to(REPO_ROOT) / rel}")
    print()
    print("Next steps:")
    print(f"  1. Edit pack.yaml - fill components, keywords, conflicts_with")
    print(f"  2. Write constraints.md - hard rules for the stack")
    print(f"  3. Implement rule functions in scripts/rules.py, add to RULES list")
    print(f"  4. (Optional) Test: enable pack in a workspace, run `python scripts/validate.py`")


if __name__ == "__main__":
    main()
