"""Export three standalone skills and one local Claude-compatible plugin. No install."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

if __package__:
    from .lib.runtime_resources import resource_path
else:
    from lib.runtime_resources import resource_path

LIB = Path(__file__).resolve().parent / "lib"
SKILLS = ("project-to-graph", "spec-to-graph", "docs-to-graph")
ASSETS = ("graph-proposal.v2.schema.json", "graph-baseline.v2.schema.json",
          "product-software.v1.json", "graph-proposal.schema.json", "graph-baseline.schema.json")
SCRIPTS = ("graph_authoring.py", "graph_authoring_oes.py", "oes_validation.py", "context_security.py")


def export(output: Path) -> None:
    """Create a new destination exclusively. Refuse existing files/dirs and symlinks."""
    resources = resource_path("templates/graph-authoring")
    sources = [resources / name for name in (*ASSETS, "authoring-contract.md", "authoring-contract-v1.md")]
    sources += [resources / "skills" / name / "SKILL.md" for name in SKILLS]
    sources += [LIB / name for name in SCRIPTS]
    for path in sources:
        if (not path.is_file()
                or any(p.is_symlink() for p in (path, *path.parents))):
            raise ValueError("Missing or unsafe bundled resource")
    output = output.absolute()
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError("Symlink export destination")
    if not output.parent.is_dir():
        raise ValueError("Create the destination parent explicitly first")
    output.mkdir(exist_ok=False)
    # If a later I/O fails, leave the partial new directory for inspection; do not
    # delete user changes that could have been made concurrently. Retry at a new path.
    (output / ".claude-plugin").mkdir()
    (output / ".claude-plugin/plugin.json").write_text(json.dumps({
        "name": "graph-authoring", "version": "0.2.0",
        "description": "Draft native OES graph proposals with checked source excerpts; never approve or apply."
    }, indent=2) + "\n", encoding="utf-8")
    for name in SKILLS:
        target = output / "skills" / name
        for subdir in ("assets", "references", "scripts"):
            (target / subdir).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resources / "skills" / name / "SKILL.md", target / "SKILL.md")
        for asset in ASSETS:
            shutil.copyfile(resources / asset, target / "assets" / asset)
        shutil.copyfile(resources / "authoring-contract.md", target / "references/authoring-contract.md")
        shutil.copyfile(resources / "authoring-contract-v1.md", target / "references/authoring-contract-v1.md")
        for script in SCRIPTS:
            shutil.copyfile(LIB / script, target / "scripts" / script)
        (target / "scripts/validate.py").write_text(
            'from pathlib import Path\nfrom graph_authoring import main\n\n'
            'if __name__ == "__main__":\n'
            '    raise SystemExit(main(resources=Path(__file__).resolve().parent.parent / "assets"))\n',
            encoding="utf-8")
    (output / "README.md").write_text(
        "# graph-authoring 0.2.0\n\n"
        "Three self-contained Agent Skills; exported resources share one source version.\n"
        "Copy a skill directory to a host-supported skills directory only after reviewing it.\n"
        "The plugin can be inspected with `claude plugin validate /absolute/export/path`\n"
        "and loaded with `claude --plugin-dir /absolute/export/path`.\n"
        "No host installation or settings changes were performed by this export.\n"
        "New proposals use contextd_graph_proposal.v2 with native oes.graph/v1 payloads.\n"
        "Legacy v1 schemas/profile remain solely for existing proposals, without automatic migration.\n"
        "Semantic extraction requires an agent with authorized tools. The bundled validator\n"
        "needs Python 3.10+, jsonschema 4.x and a trusted OES installation with Node.js 20+.\n"
        "OES supplies the graph schema, ontology and exact excerpt checks; no ontology copy is bundled.\n"
        "Native validation reads only explicitly selected local source files and exports pending copies.\n"
        "It never fetches remote sources, approves a proposal or applies canonical changes.\n"
        "A successful export is not a live-host or semantic-quality test.\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory; parent must already exist")
    args = parser.parse_args(argv)
    try:
        export(args.output)
    except (OSError, ValueError):
        print("Export refused or incomplete: inspect source resources and a fresh, non-symlink destination.", file=sys.stderr)
        return 2
    print("Exported graph-authoring; no skills were installed in a host.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
