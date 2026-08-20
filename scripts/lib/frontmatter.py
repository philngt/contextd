#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small standard-library parser for contextd's OKF frontmatter subset.

The parser intentionally accepts unknown fields. It supports the constructs
emitted by contextd templates: scalar values, flow lists/maps, nested mappings,
and block lists of shallow mappings.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple


def parse_yaml_subset(text: str) -> dict:
    data: dict = {}
    lines = text.split("\n")
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        key, separator, rest = stripped.partition(":")
        if not separator:
            i += 1
            continue
        key = key.strip()
        if not rest.strip():
            value, i = _parse_block(lines, i + 1)
            data[key] = value
            continue
        data[key] = _parse_flow(rest)
        i += 1
    return data


def _parse_flow(value: str):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_scalar(x) for x in _split_flow(inner)] if inner else []
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        out: dict = {}
        if not inner:
            return out
        for pair in _split_flow(inner):
            key, separator, item = pair.partition(":")
            if separator:
                out[key.strip()] = _scalar(item)
        return out
    return _scalar(value)


def _split_flow(value: str) -> list[str]:
    items: list[str] = []
    buffer = ""
    in_single = False
    in_double = False
    for char in value:
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        if char == "," and not in_single and not in_double:
            if buffer.strip():
                items.append(buffer.strip())
            buffer = ""
        else:
            buffer += char
    if buffer.strip():
        items.append(buffer.strip())
    return items


def _scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    comment_at = value.find(" #")
    if comment_at != -1:
        value = value[:comment_at].strip()
    return value


def _parse_block(lines: list[str], index: int) -> Tuple[Any, int]:
    count = len(lines)
    indent: Optional[int] = None
    items: list = []
    is_list = False
    while index < count:
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        current_indent = len(line) - len(line.lstrip())
        if indent is None:
            indent = current_indent
            is_list = line.strip().startswith("- ")
            if not is_list:
                return _parse_dict_block(lines, index, current_indent)
        if current_indent < indent:
            break
        stripped = line.strip()
        if not is_list or not stripped.startswith("- "):
            break
        item = stripped[2:].strip()
        if ":" in item:
            entry: dict = {}
            key, _, value = item.partition(":")
            entry[key.strip()] = _parse_flow(value)
            next_index = index + 1
            while next_index < count and lines[next_index].strip():
                nested_indent = len(lines[next_index]) - len(lines[next_index].lstrip())
                if nested_indent <= indent:
                    break
                nested = lines[next_index].strip()
                if nested.startswith("- "):
                    break
                nested_key, separator, nested_value = nested.partition(":")
                if separator:
                    entry[nested_key.strip()] = _parse_flow(nested_value)
                next_index += 1
            items.append(entry)
            index = next_index
        else:
            items.append(_scalar(item))
            index += 1
    return items, index


def _parse_dict_block(lines: list[str], index: int, indent: int) -> Tuple[dict, int]:
    result: dict = {}
    count = len(lines)
    while index < count:
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if len(line) - len(line.lstrip()) < indent:
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            break
        key, separator, rest = stripped.partition(":")
        if not separator:
            index += 1
            continue
        key = key.strip()
        if rest.strip():
            result[key] = _parse_flow(rest)
            index += 1
        else:
            value, index = _parse_block(lines, index + 1)
            result[key] = value
    return result, index


def split_frontmatter(text: str) -> tuple[Optional[dict], str]:
    """Return parsed frontmatter and body, or ``None`` for absent/invalid fences."""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return None, text
    end = normalized.find("\n---", 4)
    if end == -1:
        return None, text
    return parse_yaml_subset(normalized[4:end]), normalized[end + 4:]
