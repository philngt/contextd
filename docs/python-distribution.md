# Python distribution and publication

The distribution name is `philngt-contextd`. Python imports use `contextd`, and
the installed commands remain `contextd` and `contextd-project`. The source
layout remains `scripts/` for existing maintenance commands; the wheel exposes
no top-level `scripts` package and uses package-relative runtime imports.

The name [`contextd` on PyPI](https://pypi.org/project/contextd/) is already used
by a different project. Do not instruct users to install that distribution for
this repository. Availability of the proposed distribution name is not a
reservation, and this change does not claim a PyPI release exists.

## Build and verify locally

From a reviewed checkout:

```bash
python -m pip install -e '.[test]' 'twine>=6,<7'
python -m build
python scripts/test_distribution.py --dist-dir dist
python -m twine check --strict dist/*
```

The distribution regression suite builds wheel and source archives from a
temporary copy, installs outside the repository, and exercises the CLI,
context/explain, doctor and MCP. It checks collisions with unrelated `scripts`
and `lib` modules and an unrelated distribution's version metadata. Runtime
schemas and the manifest are bundled resources; checkout maintenance checks do
not require installed users to have `contextd.spec` or checked-in adapters.
Workspace errors remain errors. The source archive must rebuild a usable wheel.

`--dist-dir` verifies the exact wheel and source archive you intend to upload,
including their names, versions and unchanged SHA-256 digests. Use a fresh output
directory or remove obsolete artifacts yourself: the gate requires one wheel
and one source archive. Without this option the suite builds its own temporary
artifacts for ordinary CI regression checks.

Packs and agent pipeline documents are optional repository content, not copied
into the core Python package as a default project knowledge base. Point the CLI
at an existing governed workspace, as in the
[separate application example](../examples/external-project/README.md).

To install a built wheel in a separate environment, substitute its version in
this path:

```bash
python -m pip install /path/to/philngt_contextd-VERSION-py3-none-any.whl
contextd --version
```

## Source compatibility and runtime resources

Setuptools maps `scripts/` to the canonical installed `contextd` package without
moving source files. Direct commands such as `python scripts/cli.py` and existing
source-test imports remain supported. Installed imports neither alter `sys.path`
nor create global `lib` or `cmd_*` aliases. Version resolution reads this
distribution's metadata, not the unrelated PyPI distribution named `contextd`.

The build copies canonical schemas, a generated manifest and optional authoring
resources into `contextd/_resources`. No second schema or manifest source tree is
checked in. Installed authoring entry points and skill export use these resources;
semantic validation still needs the `authoring` extra and a trusted OES CLI.
The distribution tests include the optional entry point and exporter.

## Standalone binaries

PyInstaller consumes a regular installed package and its resources:

```bash
python -m pip install . 'pyinstaller==6.11.0'
pyinstaller --clean contextd.spec
python scripts/test_distribution.py --binary dist/contextd
```

On Windows, the binary path is `dist/contextd.exe`. The binary smoke runs doctor,
context, explain and MCP against a temporary project, including an invalid
workspace check. Release jobs run this smoke for each supported platform.

## Remaining publisher setup

`.github/workflows/publish-python.yml` is an explicit manual publication workflow.
It is not triggered by pushes, pull requests or GitHub Releases. Before using it,
the project owner must register an authorized
[PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/):

| Setting | Value |
|---|---|
| PyPI project | `philngt-contextd` (subject to availability and ownership) |
| GitHub owner | `philngt` |
| Repository | `contextd` |
| Workflow filename | `publish-python.yml` |
| Environment | `pypi` |

Create a version tag that contains the reviewed packaging changes and matches
`project.version`. Existing tags from before this change do not contain the new
distribution. Dispatch the workflow with `release_ref: refs/tags/vX.Y.Z`.

The build job checks the tag, distribution name and version, builds the
wheel/sdist, runs isolated installation checks against those exact artifacts,
and validates package metadata. The separate publication job receives only
those distribution artifacts and obtains
short-lived publishing credentials through the registered OIDC identity.

This task prepared the code and checks; it did not register a PyPI account,
configure its publisher, create a release tag, or dispatch publication. Those
account-bound actions require the repository owner's configured publishing
identity. See the [PyPA publication guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
