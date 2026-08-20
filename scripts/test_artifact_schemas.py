#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate generated synapse/context artifacts against shipped schemas."""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import date
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import pack_loader  # noqa: E402
from lib import task_context_engine  # noqa: E402


def _schema(name: str) -> dict:
    return json.loads((ROOT / "templates" / name).read_text(encoding="utf-8"))


def _validate(name: str, artifact: dict, schema: dict) -> None:
    validator = Draft7Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(artifact), key=lambda item: list(item.path))
    if not errors:
        return
    rendered = []
    for error in errors:
        path = "/".join(str(part) for part in error.path) or "<root>"
        rendered.append(f"{name}:{path}: {error.message}")
    raise AssertionError("\n".join(rendered))


def run() -> int:
    pack_schema = _schema("pack.schema.json")
    for manifest_path in sorted((ROOT / "packs").glob("pack-*/pack.yaml")):
        manifest = pack_loader._parse_simple_yaml(  # noqa: SLF001
            manifest_path.read_text(encoding="utf-8")
        )
        _validate(manifest_path.parent.name, manifest, pack_schema)

    with tempfile.TemporaryDirectory(prefix="contextd-schema-test-") as raw:
        output = Path(raw)
        artifact, synapse = task_context_engine.build_context_snapshot(
            task="review synapse artifact schemas",
            wiki_root=ROOT,
            workspace="default",
            packs=[],
            project_dir=ROOT,
            synapse_as_of=date(2026, 8, 20),
        )
        materialized = task_context_engine.materialize_context(
            artifact,
            output,
            synapse_snapshot=synapse,
        )
        persisted = json.loads(
            (output / ".contextd" / "context" / "current-task.json").read_text(
                encoding="utf-8",
            )
        )
        persisted_synapse = json.loads(
            (output / ".contextd" / "context" / "synapse.json").read_text(
                encoding="utf-8",
            )
        )
        assert materialized == persisted
        assert persisted_synapse == synapse
        synapse_schema = _schema("synapse.schema.json")
        _validate("synapse-returned", synapse, synapse_schema)
        _validate("synapse-persisted", persisted_synapse, synapse_schema)
        context_schema = _schema("task-context.schema.json")
        _validate("context-returned", materialized, context_schema)
        _validate("context-persisted", persisted, context_schema)
    print("ALL ARTIFACT SCHEMA TESTS PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
