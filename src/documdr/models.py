# SPDX-License-Identifier: MIT
"""Records from spec 001. Change notes are not part of these fingerprinted types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SafetyClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"


CLASS_RANK = {SafetyClass.A: 0, SafetyClass.B: 1, SafetyClass.C: 2}

FREE_TIER_CONTRIBUTOR_LIMIT = 3


@dataclass(frozen=True)
class Annotation:
    kind: str
    ref_id: str
    statement: str
    path: str
    line_number: int
    content_sha256: str
    commit_sha: str | None
    contributor_ref: str | None
    attrs: dict[str, str]


@dataclass(frozen=True)
class Exclusion:
    path: str
    reason: str
    line_number: int | None = None


@dataclass(frozen=True)
class ControlLink:
    control_id: str
    implements: list[str]
    effectiveness: str | None


@dataclass(frozen=True)
class MatrixRow:
    requirement_id: str
    statement: str
    safety_class: str
    need_id: str | None
    architecture_id: str | None
    design_id: str | None
    implementation_path: str
    implementation_commit: str | None
    implementation_content_sha256: str
    system_tests: list[str]
    unit_tests: list[str]
    integration_tests: list[str]
    risk_ids: list[str]
    gaps: list[str]
    not_applicable: list[str]


@dataclass(frozen=True)
class RiskRecord:
    risk_id: str
    statement: str
    hazard_id: str | None
    harm: str | None
    severity: str | None
    probability: str | None
    probability_not_estimated: bool
    controls: list[ControlLink]
    gaps: list[str]


@dataclass(frozen=True)
class Matrix:
    project_class: str
    rows: list[MatrixRow]
    risks: list[RiskRecord]
    project_gaps: list[str]
    exclusions: list[Exclusion]
