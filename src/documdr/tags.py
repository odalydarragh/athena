# SPDX-License-Identifier: MIT
"""Line grammar from spec 001."""

from __future__ import annotations

import re

from documdr.privacy import redact_emails

KINDS = frozenset({"REQ", "RISK", "TEST", "ARCH", "DESIGN", "SOUP", "HAZARD", "CTRL", "NEED"})

TAG_RE = re.compile(
    r"\b(?P<kind>REQ|RISK|TEST|ARCH|DESIGN|SOUP|HAZARD|CTRL|NEED)-(?P<num>[A-Za-z0-9]{1,32})\b"
)
ATTR_RE = re.compile(r"\[(?P<key>[a-z][a-z0-9_]{0,32})(?:=(?P<value>[^\]\n]{0,200}))?\]")

STATEMENT_CAP = 500


def parse_tag_line(line: str) -> tuple[str, str, str, dict[str, str]] | None:
    """Return kind, ref id, statement, and attributes. None when the line has no tag."""
    match = TAG_RE.search(line)
    if match is None or match.group("kind") not in KINDS:
        return None
    ref_id = f"{match.group('kind')}-{match.group('num')}"
    rest = line[match.end() :]
    attrs: dict[str, str] = {}
    for attr in ATTR_RE.finditer(rest):
        value = (attr.group("value") or "").strip()
        attrs[attr.group("key")] = redact_emails(value)
    first_attr = ATTR_RE.search(rest)
    region = rest[: first_attr.start()] if first_attr else rest
    statement = re.sub(r"^[\s:\-–—]+", "", region.strip())
    statement = re.sub(r"\s+", " ", statement)[:STATEMENT_CAP]
    statement = redact_emails(statement)
    return match.group("kind"), ref_id, statement, attrs
