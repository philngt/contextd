# Runbook: Release Manifest Build Failure

## Symptom

Release packaging, manifest generation, PyInstaller smoke, or editable install version detection fails from a clean checkout.

## Likely Causes

1. `.contextd/manifest.json` does not satisfy `.contextd/manifest.schema.json`.
2. `contextd.spec` is missing hidden imports or required data files.
3. Version handling depends on ignored local files.
4. Release CI builds from local generated state instead of deterministic tracked inputs.

## Diagnosis Steps

```bash
# Regenerate manifest deterministically.
python3 scripts/generate_manifest.py

# Run focused runtime smoke tests.
python3 scripts/test_contextd_runtime.py

# Build an editable/wheel smoke from checkout.
python3 -m pip wheel . --no-deps -w /tmp/contextd-wheel-smoke
python3 -m scripts.cli --version
```

Key signals to look for:
- Regenerating manifest should be deterministic or produce a reviewed diff.
- Clean checkout must not require ignored `scripts/_version.py`.
- Packaging should include schemas, templates, and CLI modules needed by `contextd context`.

## Fix

| Cause | Fix |
|-------|-----|
| Manifest schema drift | Update `.contextd/manifest.schema.json` and regenerate `.contextd/manifest.json` in the same change. |
| Missing PyInstaller import/data | Add the module or data file to `contextd.spec`, then run a smoke build. |
| Version fallback failure | Use tracked version metadata or safe fallback generation for editable installs. |
| Dirty local-only release input | Track the required file or regenerate it in CI before packaging. |

## Verification

```bash
python3 scripts/generate_manifest.py
python3 scripts/test_contextd_runtime.py
python3 -m scripts.cli context "debug release manifest" --format json --no-materialize
```

All commands should pass without relying on ignored local files.

## Escalation

Escalate if release artifacts differ across two clean checkouts at the same commit, or if the CLI works editable but fails packaged.

## Related

> Mọi link nằm trong cùng workspace (`{ws}/...`) hoặc engine docs được phép retrieve.

- [Run trace schema](../../../templates/run-trace.schema.json)
- [Manifest schema](../../../.contextd/manifest.schema.json)
- [Manifest](../../../.contextd/manifest.json)
- [PyInstaller spec](../../../contextd.spec)
