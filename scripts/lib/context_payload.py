"""The ordered, deduplicated source view shared by hashing, budgets and output.

This module does not read files, classify tasks, or apply retrieval policy.
"""
from __future__ import annotations

from typing import Dict, Iterable, List


def compiled_sources(static_docs: Iterable[Dict], referenced_docs: Iterable[Dict]) -> List[Dict]:
    """Static guidance owns a duplicate path; preserve the actual output order."""
    result: List[Dict] = []
    seen: set[str] = set()
    for group in (static_docs, referenced_docs):
        for doc in group:
            path = doc.get("path")
            if not path or path in seen:
                continue
            seen.add(path)
            result.append(doc)
    return result
