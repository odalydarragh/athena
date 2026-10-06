# SPDX-License-Identifier: MIT
"""Human approval gate and draft markdown. Spec 001."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from documdr.disclaimer import DISCLAIMER
from documdr.matrix import build_matrix, change_notes, control_snapshot, fingerprint
from documdr.models import FREE_TIER_CONTRIBUTOR_LIMIT, Matrix
from documdr.store import Store

_REASON_ORDER = (
    "approval_missing",
    "approval_rejected",
    "approval_stale",
    "free_tier_contributor_limit",
)


@dataclass(frozen=True)
class ExportDecision:
    allowed: bool
    reasons: list[str]
    change_notes: list[str]
    markdown: str | None
    fingerprint: str


def project_matrix(store: Store, tenant_id: str, project_name: str) -> tuple[object, Matrix]:
    project = store.project_by_name(tenant_id, project_name)
    matrix = build_matrix(
        store.list_annotations(tenant_id, project["id"]),
        store.list_exclusions(tenant_id, project["id"]),
        project["iec62304_class"],
    )
    return project, matrix


def record_gate(
    store: Store,
    tenant_id: str,
    project_name: str,
    *,
    signer_name: str,
    role: str,
    meaning: str,
    reason: str,
) -> str:
    project, matrix = project_matrix(store, tenant_id, project_name)
    return store.add_approval(
        tenant_id,
        project["id"],
        signer_name=signer_name,
        role=role,
        meaning=meaning,
        reason=reason,
        matrix_fingerprint=fingerprint(matrix),
        control_snapshot=control_snapshot(matrix),
    )


def decide_export(store: Store, tenant_id: str, project_name: str) -> ExportDecision:
    tenant = store.get_tenant(tenant_id)
    project, matrix = project_matrix(store, tenant_id, project_name)
    current = fingerprint(matrix)
    latest = store.latest_approval(tenant_id, project["id"])
    last_approve = store.latest_approval(tenant_id, project["id"], meaning="approve_draft")
    found: list[str] = []
    if latest is None:
        found.append("approval_missing")
    elif latest["meaning"] == "reject":
        found.append("approval_rejected")
    elif latest["matrix_fingerprint"] != current:
        found.append("approval_stale")
    if tenant["plan"] == "free" and store.contributor_count(tenant_id, project["id"]) > FREE_TIER_CONTRIBUTOR_LIMIT:
        found.append("free_tier_contributor_limit")
    reasons = [code for code in _REASON_ORDER if code in found]
    snapshot = None
    if last_approve is not None:
        snapshot = json.loads(last_approve["control_snapshot_json"])
    notes = change_notes(matrix, snapshot)
    if reasons:
        return ExportDecision(False, reasons, notes, None, current)
    rule11 = json.loads(project["rule11_json"]) if project["rule11_json"] else None
    markdown = render_markdown(matrix, notes, latest, rule11)
    return ExportDecision(True, [], notes, markdown, current)


def write_export(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    os.chmod(path, 0o600)


def render_markdown(matrix: Matrix, notes: list[str], approval: object, rule11: dict | None) -> str:
    lines = [
        "# DocuMDR draft traceability record",
        "",
        f"> {DISCLAIMER}",
        "",
        "Evidence scaling follows IEC 62304:2006+AMD1:2015 as described in spec 001.",
        "This draft does not claim presumption of conformity.",
        "",
        f"Project safety class: {matrix.project_class}",
        "",
        "## Requirements",
        "",
        "| Requirement | Class | Implementation | System tests | Gaps | Not applicable |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in matrix.rows:
        lines.append(
            "| {req} | {cls} | {path} | {tests} | {gaps} | {na} |".format(
                req=_cell(f"{row.requirement_id}: {row.statement}"),
                cls=row.safety_class,
                path=_cell(row.implementation_path),
                tests=_cell(", ".join(row.system_tests)),
                gaps=_cell(", ".join(row.gaps)),
                na=_cell(", ".join(row.not_applicable)),
            )
        )
    lines.extend(["", "## Project gaps", ""])
    if matrix.project_gaps:
        lines.extend(f"- {gap}" for gap in matrix.project_gaps)
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Risk records", ""])
    lines.append(
        "Severity and probability are shown only when a person wrote them. "
        "The compiler does not estimate or accept residual risk."
    )
    lines.append("")
    if not matrix.risks:
        lines.append("No risk annotations were scanned.")
        lines.append("")
    for risk in matrix.risks:
        lines.append(f"### {risk.risk_id}")
        lines.append("")
        lines.append(_cell(risk.statement) or "(no statement)")
        lines.append("")
        lines.append(f"- Hazard: {risk.hazard_id or 'not provided'}")
        lines.append(f"- Harm: {risk.harm or 'not provided'}")
        lines.append(f"- Severity: {risk.severity or 'not provided'}")
        if risk.probability_not_estimated:
            probability = "not_estimated"
        else:
            probability = risk.probability or "not provided"
        lines.append(f"- Probability: {probability}")
        if risk.controls:
            described = ", ".join(
                f"{control.control_id} (effectiveness: {control.effectiveness or 'not provided'})"
                for control in risk.controls
            )
            lines.append(f"- Controls: {described}")
        lines.append(f"- Gaps: {', '.join(risk.gaps) if risk.gaps else 'none'}")
        lines.append("")
    lines.extend(["## Implementation change evaluation", ""])
    if notes:
        lines.extend(f"- {note}" for note in notes)
    elif any(risk.controls for risk in matrix.risks):
        lines.append("No implementation drift detected against the last approve_draft snapshot.")
    else:
        lines.append("No software risk controls are linked, so there is no implementation snapshot to compare.")
    lines.extend(["", "## Exclusions", "", "Paths below were not stored as content.", ""])
    if matrix.exclusions:
        for item in matrix.exclusions:
            location = item.path if item.line_number is None else f"{item.path}:{item.line_number}"
            lines.append(f"- {location} ({item.reason})")
    else:
        lines.append("- None.")
    if rule11 is not None:
        lines.extend(
            [
                "",
                "## Rule 11 note",
                "",
                rule11["notice"],
                "",
                f"- Limb: {rule11['limb']}",
                f"- Impact: {rule11['impact']}",
                f"- Stated class (human): {rule11['stated_class']}",
                f"- Sentence: {rule11['sentence']}",
                f"- Differs from the sentence's class: {rule11['differs_from_stated_class']}",
            ]
        )
        if rule11.get("strictest_rule_note"):
            lines.append(f"- {rule11['strictest_rule_note']}")
    lines.extend(["", "## Approval gate", ""])
    if approval is None:
        lines.append("No approval is recorded.")
    else:
        lines.append(
            f"{approval['signer_name']} ({approval['role']}) recorded {approval['meaning']} "
            f"at {approval['created_at']}."
        )
        lines.append(
            "Approve draft accepts this draft for the customer's review trail. "
            "It is not a declaration of conformity and it is not an eIDAS qualified signature."
        )
    lines.append("")
    return "\n".join(lines)


def _cell(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("|", "/").replace("\n", " ")
