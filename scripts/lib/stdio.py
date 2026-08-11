#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Force UTF-8 stdio so CLI/MCP output survives legacy console codepages.

Windows terminals commonly default `sys.stdout`/`sys.stdin` to a legacy
codepage (e.g. cp1252), which raises UnicodeEncodeError/UnicodeDecodeError
as soon as workspace content contains non-ASCII characters (Vietnamese
text, arrows, etc. are common throughout this repo's knowledge base).

Call `configure_stdio()` first thing in every script entry point.
"""

from __future__ import annotations

import sys


def configure_stdio(errors: str = "replace") -> None:
    """Reconfigure stdin/stdout/stderr to UTF-8 where possible.

    No-op for streams that don't support `reconfigure` (e.g. io.StringIO
    used by tests via contextlib.redirect_stdout) so tests keep working
    unchanged.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors=errors)
        except (ValueError, OSError):
            pass


__all__ = ["configure_stdio"]
