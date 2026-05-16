#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
atomic_write.py - Cross-platform atomic file write + advisory lock.

Why this exists: several pipeline files (run.json rollup, evidence checkpoints,
_index.md rows) get touched by >1 actor across the pipeline. Without atomic
write + advisory lock, concurrent updates can lose data.

Three primitives:

    atomic_write_text(path, text)   - write-tmp-rename for plain text
    atomic_write_json(path, data)   - same, JSON-serialized
    with_advisory_lock(path, ...)   - context manager, exclusive lockfile

Lock semantics:
    - Lock file: {path}.lock created via O_CREAT|O_EXCL (atomic on POSIX + Win).
    - Contention: retry up to timeout_ms with 50ms backoff; raises LockTimeout.
    - Stale recovery: lock with mtime > stale_after_s (default 30s) is reclaimed.

Atomicity:
    - Tmp file written first: {path}.tmp.{pid}.{nanos}
    - os.replace(tmp, path) - atomic on Win + POSIX since Python 3.3.
    - Tmp + target MUST be on same filesystem (here: same parent dir).

Usage with the lock:

    with with_advisory_lock(run_file, timeout_ms=200):
        rollup = json.loads(run_file.read_text()) if run_file.exists() else {}
        rollup["stages_completed"].append(stage)
        atomic_write_json(run_file, rollup)
"""

from __future__ import annotations

import contextlib
import errno
import json
import os
import time
from pathlib import Path
from typing import Iterator

DEFAULT_STALE_AFTER_S = 30.0
DEFAULT_LOCK_TIMEOUT_MS = 200
DEFAULT_BACKOFF_MS = 50


class LockTimeout(RuntimeError):
    """Raised when advisory lock cannot be acquired within timeout."""


def _lock_path(target: Path) -> Path:
    return target.with_name(target.name + ".lock")


def _tmp_path(target: Path) -> Path:
    return target.with_name(
        f"{target.name}.tmp.{os.getpid()}.{time.monotonic_ns()}"
    )


def _try_acquire(lock_file: Path) -> bool:
    """Atomic create of lock file. Returns True if acquired."""
    try:
        fd = os.open(
            str(lock_file),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o644,
        )
    except FileExistsError:
        return False
    except OSError as e:
        if e.errno == errno.EEXIST:
            return False
        raise
    try:
        os.write(fd, f"{os.getpid()}\n".encode("utf-8"))
    finally:
        os.close(fd)
    return True


def _is_stale(lock_file: Path, stale_after_s: float) -> bool:
    try:
        age = time.time() - lock_file.stat().st_mtime
    except FileNotFoundError:
        return False
    return age > stale_after_s


@contextlib.contextmanager
def with_advisory_lock(
    target: Path,
    *,
    timeout_ms: int = DEFAULT_LOCK_TIMEOUT_MS,
    backoff_ms: int = DEFAULT_BACKOFF_MS,
    stale_after_s: float = DEFAULT_STALE_AFTER_S,
) -> Iterator[None]:
    """Acquire exclusive advisory lock on `target`. Releases on exit.

    Raises LockTimeout if not acquired within timeout_ms.
    Reclaims locks older than stale_after_s (assumes crashed writer).
    """
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_file = _lock_path(target)

    deadline = time.monotonic_ns() + (timeout_ms * 1_000_000)
    backoff_s = backoff_ms / 1000.0

    while True:
        if _try_acquire(lock_file):
            break

        # Already held — check if stale and reclaim if so.
        if _is_stale(lock_file, stale_after_s):
            try:
                lock_file.unlink()
            except FileNotFoundError:
                pass
            # Loop back, try acquire again.
            continue

        if time.monotonic_ns() >= deadline:
            raise LockTimeout(
                f"Could not acquire lock {lock_file} within {timeout_ms}ms"
            )
        time.sleep(backoff_s)

    try:
        yield
    finally:
        try:
            lock_file.unlink()
        except FileNotFoundError:
            pass


def atomic_write_text(target: Path, text: str) -> None:
    """Write text atomically via tmp + os.replace. Same-filesystem only."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_path(target)
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(str(tmp), str(target))
    except Exception:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()
        raise


def atomic_write_json(target: Path, data, *, indent: int = 2) -> None:
    """JSON-serialize then atomic_write_text."""
    text = json.dumps(data, ensure_ascii=False, indent=indent)
    atomic_write_text(target, text)


__all__ = [
    "LockTimeout",
    "atomic_write_text",
    "atomic_write_json",
    "with_advisory_lock",
]
