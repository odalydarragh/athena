# SPDX-License-Identifier: MIT
import json

from documdr.matrix import build_matrix, canonical, fingerprint
from documdr.tags import parse_tag_line


def test_ac01_tag_grammar_and_email_redaction():
    parsed = parse_tag_line(
        "# REQ-101: Mail ada@example.com about the halt. [class=B] [arch=ARCH-7] [risk=RISK-4]"
    )
    assert parsed is not None
    kind, ref_id, statement, attrs = parsed
    assert kind == "REQ"
    assert ref_id == "REQ-101"
    assert "ada@example.com" not in statement
    assert "[redacted-email]" in statement
    assert attrs["class"] == "B"
    assert attrs["arch"] == "ARCH-7"
    assert attrs["risk"] == "RISK-4"
    assert parse_tag_line("int halt = 1;") is None


def test_ac06_class_a_system_test_and_not_applicable(ann):
    matrix = build_matrix([ann(ref_id="REQ-1", attrs={"class": "A"})], [], "A")
    row = matrix.rows[0]
    assert row.not_applicable == [
        "architecture",
        "design",
        "detailed_design",
        "unit_verification",
        "integration_test",
    ]
    assert "system_test_missing" in row.gaps
    assert "architecture_missing" not in row.gaps
    assert "architecture" not in row.gaps

    covered = build_matrix(
        [
            ann(ref_id="REQ-1", attrs={"class": "A"}),
            ann(
                kind="TEST",
                ref_id="TEST-1",
                statement="Halt is observable.",
                line_number=2,
                attrs={"verifies": "REQ-1", "level": "system", "result": "pass"},
            ),
        ],
        [],
        "A",
    )
    assert "system_test_missing" not in covered.rows[0].gaps
    assert covered.rows[0].system_tests == ["TEST-1"]


def test_ac07_class_b_evidence(ann):
    matrix = build_matrix([ann(attrs={"class": "B"})], [], "B")
    row = matrix.rows[0]
    assert row.not_applicable == ["detailed_design"]
    for code in (
        "architecture_missing",
        "design_missing",
        "unit_verification_missing",
        "integration_test_missing",
        "system_test_missing",
    ):
        assert code in row.gaps
    assert "detailed_design_missing" not in row.gaps
    assert "software_risk_process_missing" in matrix.project_gaps


def test_ac08_class_c_detailed_design(ann):
    matrix = build_matrix(
        [
            ann(attrs={"class": "C", "arch": "ARCH-1", "design": "DESIGN-1"}),
            ann(kind="ARCH", ref_id="ARCH-1", statement="Controller", line_number=2),
            ann(kind="DESIGN", ref_id="DESIGN-1", statement="", line_number=3),
        ],
        [],
        "C",
    )
    gaps = matrix.rows[0].gaps
    assert "detailed_design_missing" in gaps
    assert "unit_verification_missing" in gaps
    assert "integration_test_missing" in gaps
    assert "architecture_missing" not in gaps
    assert "design_missing" not in gaps
    assert matrix.rows[0].not_applicable == []


def test_ac09_risk_estimates_are_never_defaulted(ann):
    bare = build_matrix(
        [ann(kind="RISK", ref_id="RISK-4", statement="Air in line.", attrs={})],
        [],
        "A",
    )
    risk = bare.risks[0]
    assert risk.severity is None
    assert risk.probability is None
    assert risk.probability_not_estimated is False
    assert "severity_not_estimated" in risk.gaps
    assert "probability_missing" in risk.gaps
    assert "medium" not in json.dumps(canonical(bare))

    declared = build_matrix(
        [
            ann(
                kind="RISK",
                ref_id="RISK-4",
                statement="Air in line.",
                attrs={"probability": "not_estimated", "severity": "serious", "harm": "embolus", "hazard": "HAZARD-1"},
            ),
            ann(kind="HAZARD", ref_id="HAZARD-1", statement="Air", line_number=2),
        ],
        [],
        "A",
    )
    recorded = declared.risks[0]
    assert recorded.severity == "serious"
    assert recorded.probability is None
    assert recorded.probability_not_estimated is True
    assert "probability_missing" not in recorded.gaps
    assert "severity_not_estimated" not in recorded.gaps


def test_ac10_passing_test_does_not_close_effectiveness(ann):
    matrix = build_matrix(
        [
            ann(ref_id="REQ-1"),
            ann(
                kind="TEST",
                ref_id="TEST-9",
                statement="Halt works.",
                line_number=2,
                attrs={"verifies": "REQ-1", "level": "system", "result": "pass"},
            ),
            ann(
                kind="RISK",
                ref_id="RISK-4",
                statement="Air in line.",
                line_number=3,
                attrs={
                    "hazard": "HAZARD-1",
                    "harm": "embolus",
                    "severity": "serious",
                    "probability": "remote",
                    "ctrl": "CTRL-2",
                },
            ),
            ann(kind="HAZARD", ref_id="HAZARD-1", statement="Air", line_number=4),
            ann(
                kind="CTRL",
                ref_id="CTRL-2",
                statement="Halt.",
                line_number=5,
                attrs={"implements": "REQ-1"},
            ),
        ],
        [],
        "A",
    )
    assert "verification_of_effectiveness_missing" in matrix.risks[0].gaps
    assert matrix.rows[0].system_tests == ["TEST-9"]


def test_ac22_lower_class_needs_rationale(ann):
    matrix = build_matrix([ann(attrs={"class": "A"})], [], "C")
    row = matrix.rows[0]
    assert "lower_class_needs_rationale" in row.gaps
    assert "architecture" in row.not_applicable
    explained = build_matrix(
        [ann(attrs={"class": "A", "class_rationale": "Isolated from the therapy path."})],
        [],
        "C",
    )
    assert "lower_class_needs_rationale" not in explained.rows[0].gaps


def test_ac23_duplicate_id_keeps_earliest_path(ann):
    matrix = build_matrix(
        [
            ann(path="b.py", line_number=1, statement="later path"),
            ann(path="a.py", line_number=9, statement="earlier path"),
        ],
        [],
        "A",
    )
    assert matrix.rows[0].statement == "earlier path"
    assert matrix.rows[0].implementation_path == "a.py"
    assert "duplicate_id:REQ-1" in matrix.project_gaps


def test_fingerprint_changes_when_content_hash_changes(ann):
    first = build_matrix([ann(content_sha256="aaa")], [], "A")
    second = build_matrix([ann(content_sha256="bbb")], [], "A")
    assert fingerprint(first) != fingerprint(second)


def test_invalid_item_class_falls_back_to_project_class(ann):
    matrix = build_matrix([ann(attrs={"class": "D"})], [], "B")
    assert matrix.rows[0].safety_class == "B"
    assert "safety_class_invalid" in matrix.rows[0].gaps
    assert "architecture_missing" in matrix.rows[0].gaps


def test_soup_fields_follow_project_class(ann):
    matrix = build_matrix(
        [ann(kind="SOUP", ref_id="SOUP-1", statement="", attrs={"title": "libc"})],
        [],
        "B",
    )
    assert "SOUP-1:soup_designator_missing" in matrix.project_gaps
    assert "SOUP-1:soup_environment_missing" in matrix.project_gaps
    assert "SOUP-1:soup_title_missing" not in matrix.project_gaps
