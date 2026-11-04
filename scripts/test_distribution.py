#!/usr/bin/env python3
"""Build/install real Python artifacts; also smoke the standalone release binary."""

from __future__ import annotations

import argparse
import email
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
import venv
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def run(command, *, cwd, env=None, input=None, expected=0):
    result = subprocess.run(
        [str(part) for part in command], cwd=cwd, env=env, input=input,
        text=True, encoding="utf-8", capture_output=True, timeout=120,
    )
    if expected is not None and result.returncode != expected:
        raise AssertionError(
            f"{command!r} exited {result.returncode}\n"
            f"stdout: {result.stdout[-6000:]}\nstderr: {result.stderr[-3000:]}")
    return result


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def release_artifacts(directory: Path, project: dict) -> tuple[Path, Path]:
    """Reject ambiguous or mismatched release inputs before installing a wheel."""
    if project["name"] != "philngt-contextd":
        raise AssertionError("Unexpected project distribution name")
    wheels = sorted(directory.glob("*.whl"))
    sdists = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1 or set(directory.iterdir()) != set(wheels + sdists):
        raise AssertionError("Distribution directory must contain exactly one wheel and one sdist")
    wheel, sdist = wheels[0], sdists[0]
    with zipfile.ZipFile(wheel) as archive:
        records = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(records) != 1:
            raise AssertionError("Wheel must contain one distribution metadata record")
        wheel_metadata = email.message_from_bytes(archive.read(records[0]))
    with tarfile.open(sdist) as archive:
        records = [member for member in archive.getmembers()
                   if member.isfile() and len(PurePosixPath(member.name).parts) == 2
                   and PurePosixPath(member.name).name == "PKG-INFO"]
        if len(records) != 1:
            raise AssertionError("Source distribution must contain one root metadata record")
        sdist_metadata = email.message_from_bytes(archive.extractfile(records[0]).read())
    expected = (project["name"], project["version"])
    for artifact, metadata in ((wheel, wheel_metadata), (sdist, sdist_metadata)):
        identity = (metadata["Name"], metadata["Version"])
        if identity != expected:
            raise AssertionError(f"{artifact.name} metadata {identity!r} does not match {expected!r}")
    return wheel, sdist


def workspace_fixture(root: Path) -> Path:
    project = root / "project"
    write(project / ".contextd/config.json", json.dumps({
        "project": "installed-smoke", "workspace": "sample",
        "knowledge_root": "../knowledge", "packs": [],
    }))
    ws = root / "knowledge/workspaces/sample"
    write(ws / "workspace.md", "# Workspace\n\n## Packs\n\nNone.\n")
    write(ws / "platform/contracts/citation-format.md",
          "# Contract: citation-format\n\n## Rule\n\nCite the governed document.\n")
    write(ws / "platform/patterns/api.md",
          "# Pattern: API\n\n## Flow\n\nValidate requests before writing.\n"
          "\n## Failure Strategy\n\nReturn a documented error.\n")
    write(ws / "projects/app/knowledge-map.md",
          "# Knowledge Map\n\n## Purpose\n\nA small API with tiếng Việt notes.\n")
    write(ws / "platform/architecture/README.md", "# Architecture\n\nOne service.\n")
    write(ws / "runbooks/README.md", "# Runbooks\n\nCheck request failures.\n")
    return project


def smoke_commands(cli: Path, root: Path, *, env=None, expected_version=None):
    """Exercise installed runtime resources and real workspace errors."""
    project = workspace_fixture(root)
    version = run([cli, "--version"], cwd=project, env=env).stdout.strip()
    if expected_version is not None:
        assert version == f"contextd {expected_version}", version
    else:
        assert version.startswith("contextd ") and "0.0.0-dev" not in version, version

    doctor = json.loads(run([cli, "doctor", "--cwd", project, "--json"],
                            cwd=project, env=env).stdout)
    assert doctor["status"] == "ok", doctor
    task = "Implement app API request validation"
    artifact = json.loads(run([cli, "context", task, "--json"],
                              cwd=project, env=env).stdout)
    assert artifact["artifact_type"] == "contextd_task_context.v1", artifact
    assert artifact["referenced_docs"], artifact
    assert all(doc["path"].startswith("workspaces/sample/")
               for doc in artifact["referenced_docs"]), artifact["referenced_docs"]
    assert (project / ".contextd/context/current-task.json").is_file()
    explanation = json.loads(run([cli, "explain", task, "--json"],
                                 cwd=project, env=env).stdout)
    assert explanation["summary"]["workspace"] == "sample", explanation
    assert explanation["selection_trace"]["selected_docs"], explanation

    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-11-25", "capabilities": {},
        "clientInfo": {"name": "installed-smoke", "version": "1"},
    }}
    response = run([cli, "mcp-server", "--cwd", project], cwd=project, env=env,
                   input=json.dumps(request) + "\n")
    messages = [json.loads(line) for line in response.stdout.splitlines() if line.strip()]
    initialized = next(message for message in messages if message.get("id") == 1)
    assert initialized["result"]["serverInfo"]["name"] == "contextd", initialized

    config_path = project / ".contextd/config.json"
    config = json.loads(config_path.read_text())
    config["workspace"] = "missing"
    config_path.write_text(json.dumps(config))
    broken = run([cli, "doctor", "--cwd", project, "--json"], cwd=project,
                 env=env, expected=1)
    assert json.loads(broken.stdout)["status"] == "error", broken.stdout
    config["workspace"] = "sample"
    config_path.write_text(json.dumps(config))
    return project


class DistributionTests(unittest.TestCase):
    artifact_directory: Path | None = None

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="contextd-distribution-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.source = cls.root / "source"
        cls.source.mkdir()
        # Include uncommitted implementation files, but no ignored build/runtime state.
        files = run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                    cwd=ROOT).stdout.split("\0")
        for relative in filter(None, files):
            source = ROOT / relative
            if source.is_file():
                destination = cls.source / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination, follow_symlinks=False)
        if cls.artifact_directory is None:
            cls.dist = cls.root / "dist"
            run([sys.executable, "-m", "build", "--no-isolation", "--sdist", "--wheel", "--outdir", cls.dist],
                cwd=cls.source)
        else:
            cls.dist = cls.artifact_directory
        try:
            import tomllib
        except ModuleNotFoundError:  # build's dependency on Python 3.10.
            import tomli as tomllib
        project = tomllib.loads((cls.source / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        cls.wheel, cls.sdist = release_artifacts(cls.dist, project)
        cls.version = project["version"]
        cls.artifact_hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in (cls.wheel, cls.sdist)}
        if cls.artifact_directory is not None:
            print("Testing exact release artifacts: " + json.dumps({
                path.name: digest for path, digest in cls.artifact_hashes.items()}), flush=True)
        cls.environment = cls.root / "venv"
        venv.EnvBuilder(with_pip=True).create(cls.environment)
        binaries = cls.environment / ("Scripts" if os.name == "nt" else "bin")
        cls.python = binaries / ("python.exe" if os.name == "nt" else "python")
        cls.cli = binaries / ("contextd.exe" if os.name == "nt" else "contextd")
        cls.project_cli = binaries / ("contextd-project.exe" if os.name == "nt" else "contextd-project")
        cls.env = dict(os.environ)
        cls.env.pop("PYTHONPATH", None)
        cls.env.pop("PYTHONHOME", None)
        cls.env["PYTHONDONTWRITEBYTECODE"] = "1"
        run([cls.python, "-m", "pip", "install", "--no-index", "--no-deps", cls.wheel],
            cwd=cls.root, env=cls.env)
        cls.foreign = cls.root / "foreign"
        for name in ("scripts", "lib"):
            write(cls.foreign / name / "__init__.py", "marker = 'foreign'\n")
        for name in ("cmd_resolve", "pack_loader", "mcp_server", "render_runtime"):
            write(cls.foreign / f"{name}.py", "marker = 'foreign'\n")
        write(cls.foreign / "contextd-9.9.9.dist-info/METADATA",
              "Metadata-Version: 2.1\nName: contextd\nVersion: 9.9.9\n")
        write(cls.foreign / "pyproject.toml", '[project]\nversion = "99.0.0"\n')
        cls.env["PYTHONPATH"] = str(cls.foreign)

    @classmethod
    def tearDownClass(cls):
        for path, expected in cls.artifact_hashes.items():
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise AssertionError(f"Release artifact changed during verification: {path}")

    def test_wheel_namespace_and_resources(self):
        with zipfile.ZipFile(self.wheel) as archive:
            names = set(archive.namelist())
            self.assertIn("contextd/cli.py", names)
            self.assertFalse(any(name.startswith("scripts/") for name in names))
            self.assertFalse(any("/test_" in name for name in names))
            self.assertIn("contextd/_resources/.contextd/manifest.json", names)
            self.assertIn("contextd/_resources/templates/task-context.schema.json", names)
            self.assertIn("contextd/_resources/templates/graph-authoring/graph-proposal.v2.schema.json", names)
            entry = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
            self.assertIn("contextd = contextd.cli:main", archive.read(entry).decode())
            for source in (self.source / "templates").rglob("*.schema.json"):
                relative = str(source.relative_to(self.source)).replace(os.sep, "/")
                self.assertEqual(source.read_bytes(), archive.read("contextd/_resources/" + relative))

    def test_imports_do_not_shadow_foreign_packages_or_change_sys_path(self):
        probe = textwrap.dedent("""
            import importlib.metadata, json, sys
            import scripts, lib, cmd_resolve, pack_loader, mcp_server, render_runtime
            foreign = {name: sys.modules[name] for name in
                       ('scripts', 'lib', 'cmd_resolve', 'pack_loader', 'mcp_server', 'render_runtime')}
            before_path = sys.path[:]
            before_modules = set(sys.modules)
            import contextd.cli, contextd.cmd_graph_project
            from contextd import pack_loader as own_loader
            from contextd.lib import contextd_version, runtime_resources, pack_validation, task_context_engine
            assert pack_validation.pack_loader is own_loader
            assert task_context_engine.pack_loader is own_loader
            assert contextd.cli.render_runtime.pack_loader is own_loader
            assert sys.path == before_path
            assert all(sys.modules[name] is module and module.marker == 'foreign'
                       for name, module in foreign.items())
            leaked = [name for name in set(sys.modules) - before_modules
                      if name == 'lib' or name.startswith(('lib.', 'cmd_', 'scripts.'))]
            assert not leaked, leaked
            assert runtime_resources.source_root() is None
            assert importlib.metadata.version('contextd') == '9.9.9'
            print(json.dumps({'version': contextd_version.get_version(),
                              'distribution': importlib.metadata.version('philngt-contextd')}))
        """)
        result = json.loads(run([self.python, "-c", probe], cwd=self.foreign, env=self.env).stdout)
        self.assertEqual(result, {"version": self.version, "distribution": self.version})

    def test_clean_entry_point_has_no_source_lookup_dependency(self):
        env = {key: value for key, value in self.env.items() if key != "PYTHONPATH"}
        result = run([self.cli, "--version"], cwd=self.root, env=env)
        self.assertEqual(result.stdout.strip(), f"contextd {self.version}")

    def test_installed_commands_and_workspace_failures(self):
        project = smoke_commands(self.cli, self.root / "smoke", env=self.env,
                                 expected_version=self.version)
        graph = json.loads(run([self.cli, "synapse", "--preview", "--json"],
                               cwd=project, env=self.env).stdout)
        seed = graph["nodes"][0]["id"]
        projection = json.loads(run([self.project_cli, "--seed", seed, "--cwd", project],
                                    cwd=project, env=self.env).stdout)
        self.assertTrue(projection["nodes"], projection)

    def test_missing_installed_resource_is_an_error(self):
        package = Path(run([self.python, "-c", "import contextd; print(contextd.__path__[0])"],
                           cwd=self.foreign, env=self.env).stdout.strip())
        resource = package / "_resources/templates/task-context.schema.json"
        payload = resource.read_bytes()
        resource.unlink()
        try:
            project = workspace_fixture(self.root / "missing-resource")
            result = run([self.cli, "doctor", "--cwd", project, "--json"],
                         cwd=project, env=self.env, expected=1)
            report = json.loads(result.stdout)
            self.assertTrue(any(issue["check"] == "runtime-resources"
                                and issue["path"] == "templates/task-context.schema.json"
                                for issue in report["issues"]), report)
        finally:
            resource.write_bytes(payload)

    def test_optional_authoring_entry_and_export_use_installed_resources(self):
        run([self.python, "-m", "contextd.cmd_graph_authoring", "--help"],
            cwd=self.foreign, env=self.env)
        output = self.root / "exported-authoring"
        run([self.python, "-m", "contextd.export_graph_authoring", "--output", output],
            cwd=self.foreign, env=self.env)
        for skill in ("project-to-graph", "spec-to-graph", "docs-to-graph"):
            self.assertTrue((output / "skills" / skill / "SKILL.md").is_file())
            self.assertTrue((output / "skills" / skill / "assets/graph-proposal.v2.schema.json").is_file())
            self.assertTrue((output / "skills" / skill / "scripts/oes_validation.py").is_file())

    def test_sdist_rebuild_preserves_runtime_resources(self):
        extracted = self.root / "sdist-source"
        with tarfile.open(self.sdist) as archive:
            archive.extractall(extracted, filter="data")
        source = next(extracted.iterdir())
        dist = self.root / "rebuilt"
        run([sys.executable, "-m", "build", "--no-isolation", "--wheel", "--outdir", dist], cwd=source)
        with zipfile.ZipFile(self.wheel) as first, zipfile.ZipFile(next(dist.glob("*.whl"))) as second:
            expected = {name: first.read(name) for name in first.namelist()
                        if name.startswith("contextd/_resources/")}
            actual = {name: second.read(name) for name in second.namelist()
                      if name.startswith("contextd/_resources/")}
            self.assertEqual(expected, actual)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--binary", type=Path, help="Smoke an already-built standalone binary")
    mode.add_argument("--dist-dir", type=Path,
                      help="Install/test the exact wheel and sdist in this directory without replacing them")
    args, test_args = parser.parse_known_args()
    if args.binary is not None:
        if test_args:
            parser.error("--binary does not accept unittest selectors")
        binary = args.binary.resolve()
        with tempfile.TemporaryDirectory(prefix="contextd-binary-smoke-") as directory:
            smoke_commands(binary, Path(directory))
        print("ok installed binary: resources, context, explain, MCP, workspace failures")
    else:
        DistributionTests.artifact_directory = args.dist_dir.resolve() if args.dist_dir else None
        unittest.main(argv=[sys.argv[0], *test_args], verbosity=2)
