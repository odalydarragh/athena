# SPDX-License-Identifier: MIT
"""Local repository walk. Git metadata comes from the local git binary only."""

from __future__ import annotations

import hashlib
import hmac
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from documdr.models import Annotation, Exclusion
from documdr.privacy import (
    exclusion_reason_for_path,
    looks_like_clinical_payload,
    looks_like_secret_line,
)
from documdr.tags import parse_tag_line

DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_MAX_FILES = 5000
_BINARY_PROBE = 8192


@dataclass(frozen=True)
class ScanResult:
    annotations: list[Annotation]
    exclusions: list[Exclusion]


def contributor_ref(salt: bytes, email: str) -> str:
    digest = hmac.new(salt, email.strip().lower().encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()[:32]


def scan_tree(
    root: Path,
    salt: bytes,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
) -> ScanResult:
    root = root.resolve()
    annotations: list[Annotation] = []
    exclusions: list[Exclusion] = []
    seen_files = 0

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        kept_dirs: list[str] = []
        for dirname in dirnames:
            child = current / dirname
            if child.is_symlink():
                exclusions.append(Exclusion(_relative(root, child), "symlink_escape"))
                continue
            relative = _relative(root, child)
            if exclusion_reason_for_path(relative / "keep.txt") == "denied_directory":
                exclusions.append(Exclusion(relative.as_posix(), "denied_directory"))
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            seen_files += 1
            if seen_files > max_files:
                exclusions.append(Exclusion(_relative(root, current / filename).as_posix(), "scan_cap"))
                return ScanResult(annotations, exclusions)
            path = current / filename
            _consider_file(root, path, salt, max_bytes, annotations, exclusions)

    return ScanResult(annotations, exclusions)


def _consider_file(
    root: Path,
    path: Path,
    salt: bytes,
    max_bytes: int,
    annotations: list[Annotation],
    exclusions: list[Exclusion],
) -> None:
    if path.is_symlink():
        try:
            resolved = path.resolve()
            resolved.relative_to(root)
        except (OSError, ValueError):
            exclusions.append(Exclusion(_relative(root, path).as_posix(), "symlink_escape"))
            return
        exclusions.append(Exclusion(_relative(root, path).as_posix(), "symlink_escape"))
        return

    try:
        relative = path.resolve().relative_to(root)
    except (OSError, ValueError):
        exclusions.append(Exclusion(path.name, "symlink_escape"))
        return

    relative_posix = relative.as_posix()
    reason = exclusion_reason_for_path(relative)
    if reason is not None:
        exclusions.append(Exclusion(relative_posix, reason))
        return

    try:
        size = path.stat().st_size
    except OSError:
        exclusions.append(Exclusion(relative_posix, "file_too_large"))
        return
    if size > max_bytes:
        exclusions.append(Exclusion(relative_posix, "file_too_large"))
        return

    try:
        raw = path.read_bytes()
    except OSError:
        exclusions.append(Exclusion(relative_posix, "file_too_large"))
        return

    if b"\x00" in raw[:_BINARY_PROBE]:
        exclusions.append(Exclusion(relative_posix, "binary"))
        return

    text = raw.decode("utf-8", errors="replace")
    if looks_like_clinical_payload(text):
        exclusions.append(Exclusion(relative_posix, "clinical_payload"))
        return

    content_sha = hashlib.sha256(raw).hexdigest()
    commit_sha, email = _git_identity(root, relative)
    ref = contributor_ref(salt, email) if email else None

    for line_number, line in enumerate(text.splitlines(), start=1):
        if looks_like_secret_line(line):
            exclusions.append(Exclusion(relative_posix, "secret_redacted", line_number))
            continue
        parsed = parse_tag_line(line)
        if parsed is None:
            continue
        kind, ref_id, statement, attrs = parsed
        annotations.append(
            Annotation(
                kind=kind,
                ref_id=ref_id,
                statement=statement,
                path=relative_posix,
                line_number=line_number,
                content_sha256=content_sha,
                commit_sha=commit_sha,
                contributor_ref=ref,
                attrs=attrs,
            )
        )


def _relative(root: Path, path: Path) -> Path:
    try:
        return path.resolve().relative_to(root)
    except (OSError, ValueError):
        return Path(path.name)


def _git_identity(root: Path, relative: Path) -> tuple[str | None, str | None]:
    """Return commit sha and author email. The email must not be stored by callers."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%H%x1f%ae", "--", relative.as_posix()],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    if completed.returncode != 0:
        return None, None
    payload = completed.stdout.strip()
    if not payload:
        return None, None
    sha, _, email = payload.partition("\x1f")
    sha = sha.strip() or None
    email = email.strip() or None
    return sha, email
