# SPDX-License-Identifier: MIT
"""Class-scaled traceability matrix. Spec 001."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass

from documdr.models import (
    CLASS_RANK,
    Annotation,
    ControlLink,
    Exclusion,
    Matrix,
    MatrixRow,
    RiskRecord,
    SafetyClass,
)

_ID_RE = re.compile(r"^(REQ|RISK|TEST|ARCH|DESIGN|SOUP|HAZARD|CTRL|NEED)-[A-Za-z0-9]{1,32}$")
_SPLIT_RE = re.compile(r"[,;\s]+")


@dataclass(frozen=True)
class EvidenceNeeds:
    architecture: bool
    design: bool
    detailed_design: bool
    unit_verification: bool
    integration_test: bool
    system_test: bool


def evidence_requirements(safety: SafetyClass) -> EvidenceNeeds:
    """IEC 62304:2006+AMD1:2015 scaling. System test applies to every class."""
    if safety is SafetyClass.A:
        return EvidenceNeeds(False, False, False, False, False, True)
    if safety is SafetyClass.B:
        return EvidenceNeeds(True, True, False, True, True, True)
    return EvidenceNeeds(True, True, True, True, True, True)


def index_annotations(annotations: list[Annotation]) -> tuple[dict[str, Annotation], list[str]]:
    grouped: dict[str, list[Annotation]] = defaultdict(list)
    for annotation in annotations:
        grouped[annotation.ref_id].append(annotation)
    chosen: dict[str, Annotation] = {}
    gaps: list[str] = []
    for ref_id, items in grouped.items():
        ordered = sorted(items, key=lambda item: (item.path, item.line_number))
        chosen[ref_id] = ordered[0]
        if len(ordered) > 1:
            gaps.append(f"duplicate_id:{ref_id}")
    return chosen, gaps


def build_matrix(
    annotations: list[Annotation],
    exclusions: list[Exclusion],
    project_class: str,
) -> Matrix:
    project = SafetyClass(project_class)
    chosen, project_gaps = index_annotations(annotations)
    rows = [
        _requirement_row(annotation, project, chosen)
        for annotation in chosen.values()
        if annotation.kind == "REQ"
    ]
    rows.sort(key=lambda row: row.requirement_id)
    risks = [
        _risk_record(annotation, chosen)
        for annotation in chosen.values()
        if annotation.kind == "RISK"
    ]
    risks.sort(key=lambda risk: risk.risk_id)
    referenced_controls = {
        control.control_id for risk in risks for control in risk.controls
    }
    for annotation in chosen.values():
        if annotation.kind == "CTRL" and annotation.ref_id not in referenced_controls:
            project_gaps.append(f"orphan_control:{annotation.ref_id}")
        if annotation.kind == "SOUP":
            project_gaps.extend(_soup_gaps(annotation, project))
    if project in (SafetyClass.B, SafetyClass.C) and not any(
        item.kind == "RISK" for item in annotations
    ):
        project_gaps.append("software_risk_process_missing")
    ordered_exclusions = sorted(
        exclusions,
        key=lambda item: (item.path, -1 if item.line_number is None else item.line_number, item.reason),
    )
    return Matrix(
        project_class=project.value,
        rows=rows,
        risks=risks,
        project_gaps=sorted(set(project_gaps)),
        exclusions=ordered_exclusions,
    )


def canonical(matrix: Matrix) -> dict:
    return {
        "exclusions": [
            {"line_number": item.line_number, "path": item.path, "reason": item.reason}
            for item in matrix.exclusions
        ],
        "project_class": matrix.project_class,
        "project_gaps": list(matrix.project_gaps),
        "risks": [
            {
                "controls": [
                    {
                        "control_id": control.control_id,
                        "effectiveness": control.effectiveness,
                        "implements": list(control.implements),
                    }
                    for control in risk.controls
                ],
                "gaps": list(risk.gaps),
                "harm": risk.harm,
                "hazard_id": risk.hazard_id,
                "probability": risk.probability,
                "probability_not_estimated": risk.probability_not_estimated,
                "risk_id": risk.risk_id,
                "severity": risk.severity,
                "statement": risk.statement,
            }
            for risk in matrix.risks
        ],
        "rows": [
            {
                "architecture_id": row.architecture_id,
                "design_id": row.design_id,
                "gaps": list(row.gaps),
                "implementation_commit": row.implementation_commit,
                "implementation_content_sha256": row.implementation_content_sha256,
                "implementation_path": row.implementation_path,
                "integration_tests": list(row.integration_tests),
                "need_id": row.need_id,
                "not_applicable": list(row.not_applicable),
                "requirement_id": row.requirement_id,
                "risk_ids": list(row.risk_ids),
                "safety_class": row.safety_class,
                "statement": row.statement,
                "system_tests": list(row.system_tests),
                "unit_tests": list(row.unit_tests),
            }
            for row in matrix.rows
        ],
    }


def fingerprint(matrix: Matrix) -> str:
    payload = json.dumps(canonical(matrix), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def control_snapshot(matrix: Matrix) -> dict[str, dict[str, str]]:
    hashes = {row.requirement_id: row.implementation_content_sha256 for row in matrix.rows}
    snapshot: dict[str, dict[str, str]] = {}
    for risk in matrix.risks:
        for control in risk.controls:
            snapshot[control.control_id] = {
                req_id: hashes[req_id] for req_id in control.implements if req_id in hashes
            }
    return snapshot


def change_notes(matrix: Matrix, snapshot: dict[str, dict[str, str]] | None) -> list[str]:
    """Implementation drift. These notes are not part of the fingerprint."""
    notes: list[str] = []
    hashes = {row.requirement_id: row.implementation_content_sha256 for row in matrix.rows}
    for risk in matrix.risks:
        for control in risk.controls:
            saved = None if snapshot is None else snapshot.get(control.control_id)
            if saved is None:
                notes.append(f"{control.control_id}: verification_of_implementation_missing")
                continue
            drifted = False
            for req_id in control.implements:
                if hashes.get(req_id) != saved.get(req_id):
                    drifted = True
            if drifted:
                notes.append(f"{control.control_id}: reverification_required")
    return sorted(set(notes))


def _requirement_row(
    annotation: Annotation,
    project: SafetyClass,
    chosen: dict[str, Annotation],
) -> MatrixRow:
    gaps: list[str] = []
    if not annotation.statement.strip():
        gaps.append("requirement_statement_missing")
    item_class, class_gaps = _item_class(annotation.attrs, project)
    gaps.extend(class_gaps)
    needs = evidence_requirements(item_class)
    not_applicable = _not_applicable(needs)

    tests = [
        item
        for item in chosen.values()
        if item.kind == "TEST" and annotation.ref_id in _id_list(item.attrs.get("verifies", ""))[0]
    ]
    system_ids, system_gap = _level_status(tests, "system")
    unit_ids, unit_gap = _level_status(tests, "unit")
    integration_ids, integration_gap = _level_status(tests, "integration")
    if any(not item.attrs.get("level") or item.attrs.get("level") not in {"unit", "integration", "system"} for item in tests):
        gaps.append("test_level_unrecognised")
    if needs.system_test and system_gap:
        gaps.append(system_gap)
    if needs.unit_verification and unit_gap:
        gaps.append(unit_gap)
    if needs.integration_test and integration_gap:
        gaps.append(integration_gap)

    architecture_id = _linked_id(annotation.attrs, "arch", "ARCH", chosen, gaps, "architecture", needs.architecture)
    design_id = _linked_id(annotation.attrs, "design", "DESIGN", chosen, gaps, "design", needs.design)
    if needs.detailed_design and design_id and design_id in chosen and chosen[design_id].kind == "DESIGN":
        if not chosen[design_id].statement.strip():
            gaps.append("detailed_design_missing")
    need_id, need_bad = _optional_id(annotation.attrs.get("need", ""), "NEED")
    if need_bad:
        gaps.append("malformed_link")
    risk_ids, risk_bad = _id_list(annotation.attrs.get("risk", ""))
    if risk_bad:
        gaps.append("malformed_link")
    if annotation.commit_sha is None:
        gaps.append("commit_identity_missing")

    return MatrixRow(
        requirement_id=annotation.ref_id,
        statement=annotation.statement,
        safety_class=item_class.value,
        need_id=need_id,
        architecture_id=architecture_id,
        design_id=design_id,
        implementation_path=annotation.path,
        implementation_commit=annotation.commit_sha,
        implementation_content_sha256=annotation.content_sha256,
        system_tests=system_ids,
        unit_tests=unit_ids,
        integration_tests=integration_ids,
        risk_ids=risk_ids,
        gaps=sorted(set(gaps)),
        not_applicable=not_applicable,
    )


def _risk_record(annotation: Annotation, chosen: dict[str, Annotation]) -> RiskRecord:
    gaps: list[str] = []
    hazard_id, hazard_bad = _optional_id(annotation.attrs.get("hazard", ""), "HAZARD")
    if hazard_bad or hazard_id is None or hazard_id not in chosen or chosen[hazard_id].kind != "HAZARD":
        gaps.append("hazard_missing")
        hazard_id = None
    harm = annotation.attrs.get("harm", "").strip() or None
    if harm is None:
        gaps.append("harm_missing")
    severity = annotation.attrs.get("severity", "").strip() or None
    if severity is None:
        gaps.append("severity_not_estimated")
    probability_raw = annotation.attrs.get("probability", "").strip()
    probability_not_estimated = probability_raw == "not_estimated"
    probability = probability_raw or None
    if not probability_not_estimated and probability is None:
        gaps.append("probability_missing")
    control_ids, control_bad = _id_list(annotation.attrs.get("ctrl", ""))
    if control_bad:
        gaps.append("malformed_link")
    controls: list[ControlLink] = []
    if not control_ids:
        gaps.append("risk_control_missing")
    missing_effectiveness = False
    missing_control = False
    for control_id in control_ids:
        control = chosen.get(control_id)
        if control is None or control.kind != "CTRL":
            missing_control = True
            continue
        implements, implements_bad = _id_list(control.attrs.get("implements", ""))
        if implements_bad:
            gaps.append("malformed_link")
        effectiveness = control.attrs.get("effectiveness", "").strip() or None
        if effectiveness is None:
            missing_effectiveness = True
        controls.append(ControlLink(control_id, implements, effectiveness))
    if missing_control:
        gaps.append("risk_control_missing")
    if missing_effectiveness:
        gaps.append("verification_of_effectiveness_missing")
    controls.sort(key=lambda item: item.control_id)
    return RiskRecord(
        risk_id=annotation.ref_id,
        statement=annotation.statement,
        hazard_id=hazard_id if hazard_id in chosen else None,
        harm=harm,
        severity=severity,
        probability=None if probability_not_estimated else probability,
        probability_not_estimated=probability_not_estimated,
        controls=controls,
        gaps=sorted(set(gaps)),
    )


def _soup_gaps(annotation: Annotation, project: SafetyClass) -> list[str]:
    gaps: list[str] = []
    if not annotation.attrs.get("title", "").strip():
        gaps.append(f"{annotation.ref_id}:soup_title_missing")
    if not annotation.attrs.get("designator", "").strip():
        gaps.append(f"{annotation.ref_id}:soup_designator_missing")
    if project in (SafetyClass.B, SafetyClass.C) and not annotation.attrs.get("environment", "").strip():
        gaps.append(f"{annotation.ref_id}:soup_environment_missing")
    return gaps


def _item_class(attrs: dict[str, str], project: SafetyClass) -> tuple[SafetyClass, list[str]]:
    raw = attrs.get("class", "").strip()
    if not raw:
        return project, []
    try:
        item = SafetyClass(raw)
    except ValueError:
        return project, ["safety_class_invalid"]
    gaps: list[str] = []
    if CLASS_RANK[item] < CLASS_RANK[project] and not attrs.get("class_rationale", "").strip():
        gaps.append("lower_class_needs_rationale")
    return item, gaps


def _not_applicable(needs: EvidenceNeeds) -> list[str]:
    names = []
    if not needs.architecture:
        names.append("architecture")
    if not needs.design:
        names.append("design")
    if not needs.detailed_design:
        names.append("detailed_design")
    if not needs.unit_verification:
        names.append("unit_verification")
    if not needs.integration_test:
        names.append("integration_test")
    return names


def _level_status(tests: list[Annotation], level: str) -> tuple[list[str], str | None]:
    matched = [item for item in tests if item.attrs.get("level") == level]
    ids = sorted(item.ref_id for item in matched)
    if not matched:
        return [], f"{_level_gap_prefix(level)}_missing" if level != "system" else "system_test_missing"
    if any(item.attrs.get("result") == "pass" for item in matched):
        return ids, None
    if any(item.attrs.get("result") == "fail" for item in matched):
        code = "system_test_failed" if level == "system" else f"{_level_gap_prefix(level)}_failed"
        return ids, code
    code = "system_test_result_missing" if level == "system" else f"{_level_gap_prefix(level)}_result_missing"
    return ids, code


def _level_gap_prefix(level: str) -> str:
    if level == "unit":
        return "unit_verification"
    if level == "integration":
        return "integration_test"
    return "system_test"


def _linked_id(
    attrs: dict[str, str],
    key: str,
    kind: str,
    chosen: dict[str, Annotation],
    gaps: list[str],
    label: str,
    required: bool,
) -> str | None:
    identifier, bad = _optional_id(attrs.get(key, ""), kind)
    if bad:
        gaps.append("malformed_link")
    if not required:
        return identifier
    if identifier is None:
        gaps.append(f"{label}_missing")
        return None
    target = chosen.get(identifier)
    if target is None or target.kind != kind:
        gaps.append(f"{label}_undefined")
    return identifier


def _optional_id(raw: str, kind: str) -> tuple[str | None, bool]:
    value = raw.strip()
    if not value:
        return None, False
    if _ID_RE.fullmatch(value) and value.startswith(kind + "-"):
        return value, False
    return None, True


def _id_list(raw: str) -> tuple[list[str], bool]:
    value = raw.strip()
    if not value:
        return [], False
    good: list[str] = []
    bad = False
    for token in _SPLIT_RE.split(value):
        if not token:
            continue
        if _ID_RE.fullmatch(token):
            good.append(token)
        else:
            bad = True
    return sorted(set(good)), bad
