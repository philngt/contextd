#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a manifest-v3 pack skeleton.

Usage:
    python scripts/scaffold-pack.py pack-mobile-flutter

The v3 skeleton deliberately has one canonical knowledge file. Retrieval lives
in pack.yaml; principles, mental models, standards, failure signals, evidence,
and stop conditions live in knowledge.md. This keeps runtime slicing possible
and avoids seven overlapping prose files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

from lib.stdio import configure_stdio  # noqa: E402


PACKS_DIR = REPO_ROOT / "packs"
TEMPLATE_PACK_YAML = REPO_ROOT / "templates" / "pack.yaml"
TEMPLATE_PACK_KNOWLEDGE = REPO_ROOT / "templates" / "pack-knowledge.md"
NAME_RE = re.compile(r"^pack-[a-z0-9][a-z0-9-]*$")


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _render_template(path: Path, pack_name: str) -> str:
    if not path.is_file():
        die(f"Template missing: {path.relative_to(REPO_ROOT)}")
    return path.read_text(encoding="utf-8").replace(
        "pack-{your-name}", pack_name,
    )


def _rules_template(pack_name: str) -> str:
    short = pack_name.removeprefix("pack-").replace("-", "_")
    return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{pack_name} deterministic validator rules.

Document every implemented rule ID in knowledge.md and expose each rule in
RULES. Keep static checks narrow; leave semantic judgment to review/evals.
"""

from __future__ import annotations

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


# Example:
# def rule_{short}_example(file_path: Path, lines: List[str],
#                          ctx: Dict) -> List[Dict]:
#     return []


RULES: List = [
    # rule_{short}_example,
]
'''


def _readme_template(pack_name: str) -> str:
    return f"""# {pack_name}

{{One-line description of the workflow or artifact this pack owns.}}

## When to enable

- {{Concrete signal that this pack owns the task.}}
- {{Second concrete signal.}}

## When not to enable

- {{Neighboring concern owned by another pack.}}
- {{Task that does not need this pack's guidance.}}

## What it adds

- `knowledge.md` — canonical principles, mental models, standards, failure
  signals, evidence requirements, and stop conditions.
- `pack.yaml#retrieval` — component-to-document routes.
- `scripts/rules.py` — deterministic checks whose IDs are documented in
  `knowledge.md`.

## Retrieval behavior

`pack.yaml#keywords` selects components. Runtime loads Global Principles plus
only the selected `## Component: ...` sections, then follows their retrieval
routes inside the active workspace.

## Verification

```bash
contextd pack-validate --pack {pack_name} --format text
contextd context "{{representative task}}" --preview --format json
contextd explain "{{representative task}}" --format text
```

## Related

- Pack mechanism: [`packs/README.md`](../README.md)
- Cross-cutting principles: [`agents/cross-cutting-principles.md`](../../agents/cross-cutting-principles.md)
"""


def main() -> None:
    configure_stdio()
    if len(sys.argv) != 2:
        die("Usage: python scripts/scaffold-pack.py <pack-name>")

    name = sys.argv[1].strip()
    if not NAME_RE.fullmatch(name):
        die(
            f"Invalid pack name '{name}'. Must match "
            "`pack-[a-z0-9][a-z0-9-]*`.",
        )

    pack_dir = PACKS_DIR / name
    if pack_dir.exists():
        die(f"Pack already exists: {pack_dir.relative_to(REPO_ROOT)}")

    (pack_dir / "scripts").mkdir(parents=True)
    (pack_dir / "pack.yaml").write_text(
        _render_template(TEMPLATE_PACK_YAML, name), encoding="utf-8",
    )
    (pack_dir / "knowledge.md").write_text(
        _render_template(TEMPLATE_PACK_KNOWLEDGE, name), encoding="utf-8",
    )
    (pack_dir / "README.md").write_text(
        _readme_template(name), encoding="utf-8",
    )
    (pack_dir / "scripts" / "rules.py").write_text(
        _rules_template(name), encoding="utf-8",
    )

    print(f"[OK] Pack scaffolded: {pack_dir.relative_to(REPO_ROOT)}")
    print("Files created:")
    for relative in ("README.md", "pack.yaml", "knowledge.md", "scripts/rules.py"):
        print(f"  {pack_dir.relative_to(REPO_ROOT) / relative}")
    print("Next steps:")
    print("  1. Replace manifest scope, components, keywords, and retrieval routes.")
    print("  2. Replace every knowledge placeholder with decision-dense guidance.")
    print("  3. Implement validators only where deterministic checks add value.")
    print(f"  4. Run `contextd pack-validate --pack {name} --format text`.")


if __name__ == "__main__":
    main()
