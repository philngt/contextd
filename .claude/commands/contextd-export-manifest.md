# Export Manifest

Generate `.contextd/manifest.json` from canonical sources (`.claude/commands/*.md`, `.claude/agents/*.md`, `packs/*/pack.yaml`, `agents/pipeline/*.md`).

```
/contextd-export-manifest [--dry-run]
```

| Flag | Description |
|------|-------------|
| `--dry-run` | Print manifest to stdout without writing file |

---

## Behavior

1. Parse `.claude/commands/*.md` → extract title from first H1.
2. Parse `.claude/agents/*.md` → extract YAML frontmatter (`name`, `description`, `tools`, `model`).
3. Parse `packs/*/pack.yaml` → name, version, description, components.
4. Parse `agents/pipeline/*.md` → pipeline doc index.
5. Write `.contextd/manifest.json` (or print if `--dry-run`).

Manifest is a **generated index**, not single source of truth. Canonical content remains in the markdown files it references.

---

## Verification

After running, confirm counts match:

```bash
python scripts/generate_manifest.py --dry-run | python -c "
import json, sys
d = json.load(sys.stdin)
print(f'commands={len(d[\"commands\"])} agents={len(d[\"agents\"])} packs={len(d[\"packs\"])}')
"
```

Counts should match:
- `commands` == number of `.claude/commands/*.md` files (excluding `README.md`)
- `agents` == number of `.claude/agents/*.md` files
- `packs` == number of `packs/*/` directories with `pack.yaml`
