# SPDX-License-Identifier: MIT
"""Denylist for paths, secrets, and clinical payloads. Spec 001 scan rules."""

from __future__ import annotations

import re
from pathlib import Path

DENIED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".documdr",
        ".pytest_cache",
        "phi",
        "patient",
        "patients",
        "dicom",
        "fhir",
        "hl7",
        "clinical-data",
        "ehr",
        "patient-data",
    }
)

CLINICAL_SUFFIXES = frozenset(
    {".dcm", ".dicom", ".hl7", ".edf", ".nii", ".nii.gz"}
)

SECRET_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".kdbx", ".sqlite", ".sqlite3", ".db"})

SECRET_FILENAMES = frozenset(
    {"id_rsa", "id_ed25519", "credentials.json", "service-account.json"}
)

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

SECRET_LINE_RE = re.compile(
    r"(?i)(api[_-]?key|secret|password|passwd|token|private[_-]?key|authorization)"
    r"\s*[:=]\s*\S{8,}"
    r"|-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
    r"|ghp_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}"
    r"|glpat-[A-Za-z0-9\-]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|sk_live_[A-Za-z0-9]{8,}"
)

_FHIR_MARKERS = ('"Patient"', '"Observation"', '"Condition"', '"DiagnosticReport"')


def redact_emails(text: str) -> str:
    return EMAIL_RE.sub("[redacted-email]", text)


def looks_like_secret_line(line: str) -> bool:
    return SECRET_LINE_RE.search(line) is not None


def looks_like_clinical_payload(text: str) -> bool:
    """True for HL7 messages and FHIR patient resources. The word Patient alone is not enough."""
    sample = text[:65536]
    head = sample[:800]
    if "MSH|" in head:
        return True
    if '"resourceType"' in sample and any(marker in sample for marker in _FHIR_MARKERS):
        return True
    return False


def _ignored_suffix(name: str) -> str | None:
    lower = name.lower()
    if lower.endswith(".nii.gz"):
        return ".nii.gz"
    suffix = Path(lower).suffix
    if suffix in CLINICAL_SUFFIXES or suffix in SECRET_SUFFIXES:
        return suffix
    return None


def exclusion_reason_for_path(relative: Path) -> str | None:
    """Return a reason when the file must not be read. None means the content may be opened."""
    parts = [part.lower() for part in relative.parts]
    if any(part in DENIED_DIRECTORIES for part in parts[:-1]):
        return "denied_directory"
    name = relative.name
    lower_name = name.lower()
    if lower_name == ".env" or lower_name.startswith(".env."):
        return "secret_filename"
    if lower_name in SECRET_FILENAMES:
        return "secret_filename"
    suffix = _ignored_suffix(name)
    if suffix in CLINICAL_SUFFIXES:
        return "clinical_extension"
    if suffix in SECRET_SUFFIXES:
        return "denied_file_type"
    return None
