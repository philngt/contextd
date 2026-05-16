#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pack-event-driven — Layer 1 validator rules.

Loaded dynamically by `scripts/validate.py` via `scripts/pack_loader.py` when
the active workspace opts into this pack (in workspace.md `## Packs` section).

Each rule is a function:
    rule_<id>(file_path: Path, lines: List[str], ctx: Dict) -> List[Dict]

Rules are exposed via the module-level `RULES` list, which `pack_loader.py`
imports and appends to the global `ALL_RULES`.

Rule IDs: prefixed `pack-event-driven-`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List


def _vio(rule: str, severity: str, file_path: Path, lineno: int,
         snippet: str, message: str) -> Dict:
    return {
        "rule": rule,
        "severity": severity,
        "file": file_path.as_posix(),
        "line": lineno,
        "snippet": snippet.strip()[:200],
        "message": message,
    }


def _strip_line_comment(line: str) -> str:
    idx = line.find("//")
    if idx >= 0:
        return line[:idx]
    return line


# ---------------------------------------------------------------------------
# Kafka rules
# ---------------------------------------------------------------------------

KAFKA_TOPIC_LITERAL = re.compile(
    r'"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+){1,})"'
)
KAFKA_CONFIG_READ_HINT = re.compile(
    r"(@Value|getProperty|getString|getConfig|env\.|System\.getenv|"
    r"@ConfigurationProperties|propertySource|ConfigMap|application\.yml)",
    re.IGNORECASE,
)


def rule_kafka_hardcoded_topics(file_path: Path, lines: List[str],
                                ctx: Dict) -> List[Dict]:
    out = []
    for i, raw in enumerate(lines, start=1):
        line = _strip_line_comment(raw)
        if KAFKA_CONFIG_READ_HINT.search(line):
            continue
        if not re.search(r"(KafkaTemplate|@KafkaListener|topics\s*=|"
                         r"send\s*\(|subscribe\s*\(|produce\s*\(|consume\s*\()",
                         line, re.IGNORECASE):
            if not re.search(r"\btopic[A-Z_a-z]*\s*=\s*\"", line):
                continue
        for m in KAFKA_TOPIC_LITERAL.finditer(line):
            literal = m.group(1)
            if any(ch.isupper() for ch in literal):
                continue
            out.append(_vio(
                "pack-event-driven-kafka-no-hardcoded-topic", "error",
                file_path, i, raw,
                f"Hardcoded Kafka topic literal '{literal}'. "
                "Read from config (@Value / properties)."
            ))
    return out


COMMIT_CALL = re.compile(r"\b(commitSync|commitAsync)\s*\(")
PROCESS_HINT = re.compile(
    r"\b(process|handle|forEach|for\s*\(|while\s*\(|onMessage|"
    r"send\s*\(|publish\s*\()", re.IGNORECASE
)


def rule_kafka_offset_commit_position(file_path: Path, lines: List[str],
                                      ctx: Dict) -> List[Dict]:
    out = []
    depth = 0
    block_stack: List[List] = [[]]
    for i, raw in enumerate(lines, start=1):
        line = _strip_line_comment(raw)
        if COMMIT_CALL.search(line):
            block_stack[-1].append((i, "commit"))
        if PROCESS_HINT.search(line) and not COMMIT_CALL.search(line):
            block_stack[-1].append((i, "process"))
        opens = line.count("{")
        closes = line.count("}")
        for _ in range(opens):
            block_stack.append([])
            depth += 1
        for _ in range(closes):
            if block_stack:
                events = block_stack.pop()
                first_process = next((ln for ln, k in events if k == "process"),
                                     None)
                for ln, k in events:
                    if k == "commit" and (first_process is None or
                                          ln < first_process):
                        snippet = lines[ln - 1] if ln - 1 < len(lines) else ""
                        out.append(_vio(
                            "pack-event-driven-kafka-commit-before-process",
                            "error", file_path, ln, snippet,
                            "Offset commit appears before message processing "
                            "in the enclosing block — data-loss risk."
                        ))
            if depth > 0:
                depth -= 1
            if not block_stack:
                block_stack.append([])
    return out


def rule_kafka_dlq_present(file_path: Path, lines: List[str],
                           ctx: Dict) -> List[Dict]:
    text = "\n".join(lines)
    is_consumer = bool(re.search(
        r"(@KafkaListener|KafkaConsumer|ConsumerRecord|@StreamListener)",
        text)) or bool(re.search(r"\bpoll\s*\(", text))
    if not is_consumer:
        return []
    if re.search(r"(?i)(dlq|deadLetter|\.dlq\.|\.dlq\b)", text):
        return []
    return [_vio(
        "pack-event-driven-kafka-dlq-required", "error", file_path, 1,
        lines[0] if lines else "",
        "Kafka consumer detected but no DLQ branch found "
        "(no reference to 'dlq' / 'deadLetter')."
    )]


PER_MESSAGE_LOOP = re.compile(
    r"\bfor\s*\(\s*\w[\w<>,\s]*\s+\w+\s*:\s*(\w*[Mm]essages?\w*)\s*\)"
)
BATCH_HINT = re.compile(r"(batch|max\.poll\.records|MAX_POLL_RECORDS|"
                        r"setBatchListener|@KafkaListener\([^)]*containerFactory)",
                        re.IGNORECASE)


def rule_kafka_batch_processing(file_path: Path, lines: List[str],
                                ctx: Dict) -> List[Dict]:
    text = "\n".join(lines)
    if not BATCH_HINT.search(text):
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        m = PER_MESSAGE_LOOP.search(raw)
        if m:
            out.append(_vio(
                "pack-event-driven-kafka-batch-processing", "warn",
                file_path, i, raw,
                f"Per-message loop over '{m.group(1)}' in batch-mode "
                "consumer — verify batch processing intent."
            ))
    return out


# ---------------------------------------------------------------------------
# MQTT rules
# ---------------------------------------------------------------------------

MQTT_INLINE_TOPIC = re.compile(
    r'("topic/[^"]*"\s*\+|\+\s*"topic/[^"]*"|'
    r'String\.format\s*\(\s*"topic/[^"]*"|'
    r'`topic/[^`]*\$\{|f"topic/[^"]*\{)'
)
MQTT_TOPIC_HELPER_HINT = re.compile(
    r"(buildTopic|topicFor|MqttTopic\.|TopicFormatter|topicHelper)",
    re.IGNORECASE
)


def rule_mqtt_no_inline_construction(file_path: Path, lines: List[str],
                                     ctx: Dict) -> List[Dict]:
    out = []
    for i, raw in enumerate(lines, start=1):
        line = _strip_line_comment(raw)
        if MQTT_TOPIC_HELPER_HINT.search(line):
            continue
        if MQTT_INLINE_TOPIC.search(line):
            out.append(_vio(
                "pack-event-driven-mqtt-no-inline-topic", "error",
                file_path, i, raw,
                "MQTT topic appears to be built inline. "
                "Use the contract format helper instead."
            ))
    return out


MQTT_TOPIC_LITERAL = re.compile(r'"topic/[^"]*/up/([a-zA-Z0-9_\-]+)"')


def rule_mqtt_only_registered_types(file_path: Path, lines: List[str],
                                    ctx: Dict) -> List[Dict]:
    registered = ctx.get("mqtt_types") or []
    if not registered:
        return []
    out = []
    for i, raw in enumerate(lines, start=1):
        for m in MQTT_TOPIC_LITERAL.finditer(raw):
            t = m.group(1)
            if t.startswith("{") or t.startswith("$"):
                continue
            if t not in registered:
                out.append(_vio(
                    "pack-event-driven-mqtt-unregistered-type", "error",
                    file_path, i, raw,
                    f"MQTT type '{t}' is not in the registered types list "
                    f"({', '.join(registered)})."
                ))
    return out


# Module-level export for pack_loader
RULES = [
    rule_kafka_hardcoded_topics,
    rule_kafka_offset_commit_position,
    rule_kafka_dlq_present,
    rule_kafka_batch_processing,
    rule_mqtt_no_inline_construction,
    rule_mqtt_only_registered_types,
]
