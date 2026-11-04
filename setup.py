"""Bundle runtime resources without keeping generated copies in source control."""

from pathlib import Path
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py


ROOT = Path(__file__).resolve().parent


class BuildRuntime(build_py):
    def find_package_modules(self, package, package_dir):
        # Source tests are not an installed public API.
        modules = super().find_package_modules(package, package_dir)
        return [module for module in modules if not module[1].startswith("test_")]

    def run(self):
        super().run()
        package = Path(self.build_lib) / "contextd"
        resources = package / "_resources"
        schemas = resources / "templates"
        schemas.mkdir(parents=True, exist_ok=True)
        sources = set((ROOT / "templates").rglob("*.schema.json"))
        sources.update(path for path in (ROOT / "templates" / "graph-authoring").rglob("*")
                       if path.is_file())
        for source in sorted(sources):
            destination = schemas / source.relative_to(ROOT / "templates")
            destination.parent.mkdir(parents=True, exist_ok=True)
            self.copy_file(str(source), str(destination))
        metadata = resources / ".contextd"
        metadata.mkdir(parents=True, exist_ok=True)
        self.copy_file(str(ROOT / ".contextd" / "manifest.schema.json"),
                       str(metadata / "manifest.schema.json"))
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_manifest.py"),
             "--output", str((metadata / "manifest.json").resolve())],
            cwd=ROOT, check=True, stdout=subprocess.PIPE, text=True,
        )
        (package / "_version.py").write_text(
            f"__version__ = {self.distribution.get_version()!r}\n", encoding="utf-8")


setup(cmdclass={"build_py": BuildRuntime})
