#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_atomic_write.py - Stress test for lib/atomic_write.

Test 1: N workers x M iters each append a tagged item to a shared JSON list.
        Expected: list has N*M items, no duplicates, no missing pairs.

Test 2: lock currently held -> LockTimeout raised within budget.

Test 3: stale lock (mtime > 30s) auto-reclaimed.

Run:
    python scripts/test_atomic_write.py
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.atomic_write import (  # noqa: E402
    LockTimeout,
    atomic_write_json,
    with_advisory_lock,
)


def _worker(target: str, worker_id: int, iters: int) -> int:
    """Append `iters` items tagged with worker_id to the shared JSON file."""
    path = Path(target)
    successes = 0
    for i in range(iters):
        for _ in range(20):  # outer retry around LockTimeout
            try:
                with with_advisory_lock(path, timeout_ms=2000):
                    if path.exists():
                        try:
                            data = json.loads(path.read_text(encoding="utf-8"))
                        except json.JSONDecodeError:
                            data = []
                    else:
                        data = []
                    data.append({"w": worker_id, "i": i})
                    atomic_write_json(path, data)
                    successes += 1
                break
            except LockTimeout:
                time.sleep(0.05)
        else:
            print(
                f"  [w{worker_id}] iter {i} exhausted retries", file=sys.stderr
            )
    return successes


def test_stress(num_workers: int = 4, iters: int = 25) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "shared.json"
        expected = num_workers * iters
        print(f"  {num_workers} workers x {iters} iters = {expected} writes")

        start = time.monotonic()
        ctx = mp.get_context("spawn")
        with ctx.Pool(num_workers) as pool:
            results = pool.starmap(
                _worker,
                [(str(target), wid, iters) for wid in range(num_workers)],
            )
        elapsed = time.monotonic() - start

        successes = sum(results)
        data = json.loads(target.read_text(encoding="utf-8"))
        actual = len(data)
        print(
            f"  successes reported: {successes}, items in file: {actual}, "
            f"elapsed: {elapsed:.2f}s"
        )

        if actual != expected:
            print(
                f"  FAIL: expected {expected}, got {actual} "
                f"(lost {expected - actual})",
                file=sys.stderr,
            )
            return False

        seen = {(d["w"], d["i"]) for d in data}
        missing = [
            (w, i)
            for w in range(num_workers)
            for i in range(iters)
            if (w, i) not in seen
        ]
        if missing:
            print(f"  FAIL: missing pairs: {missing[:5]}...", file=sys.stderr)
            return False
        if len(seen) != actual:
            print(
                f"  FAIL: duplicates detected ({actual - len(seen)})",
                file=sys.stderr,
            )
            return False
        return True


def test_lock_timeout() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "x.json"
        target.write_text("{}", encoding="utf-8")
        lock_path = target.with_name(target.name + ".lock")
        lock_path.touch()  # fresh mtime - not stale
        try:
            with with_advisory_lock(target, timeout_ms=150):
                print("  FAIL: expected LockTimeout", file=sys.stderr)
                return False
        except LockTimeout:
            print("  OK: LockTimeout raised")
        finally:
            with __import__("contextlib").suppress(FileNotFoundError):
                lock_path.unlink()
        return True


def test_stale_lock_reclaim() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "y.json"
        lock_path = target.with_name(target.name + ".lock")
        lock_path.touch()
        old = time.time() - 60.0
        os.utime(str(lock_path), (old, old))
        try:
            with with_advisory_lock(target, timeout_ms=200):
                pass
        except LockTimeout:
            print("  FAIL: stale lock not reclaimed", file=sys.stderr)
            return False
        if lock_path.exists():
            print("  FAIL: lock not cleaned on release", file=sys.stderr)
            return False
        print("  OK: stale lock reclaimed + cleaned")
        return True


def main() -> int:
    print("Test 1: stress")
    ok1 = test_stress(num_workers=4, iters=25)
    print("\nTest 2: lock timeout")
    ok2 = test_lock_timeout()
    print("\nTest 3: stale lock reclaim")
    ok3 = test_stale_lock_reclaim()
    print()
    if ok1 and ok2 and ok3:
        print("ALL TESTS PASSED")
        return 0
    print("SOME TESTS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
