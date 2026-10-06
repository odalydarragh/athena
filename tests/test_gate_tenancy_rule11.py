# SPDX-License-Identifier: MIT
import json
import stat
from pathlib import Path

from documdr.cli import main
from documdr.disclaimer import DISCLAIMER, ERASURE_LIMIT
from documdr.export import decide_export, record_gate
from documdr.models import Annotation
from documdr.rule11 import assess_rule11
from documdr.store import Store


def _annotation(ref: str, contributor: str | None, line: int) -> Annotation:
    return Annotation(
        kind="REQ",
        ref_id=ref,
        statement="The module shall halt.",
        path=f"{ref}.c",
        line_number=line,
        content_sha256=f"hash-{ref}",
        commit_sha="commit-1",
        contributor_ref=contributor,
        attrs={"class": "A"},
    )


def _test_for(ref: str) -> Annotation:
    return Annotation(
        kind="TEST",
        ref_id=f"TEST-{ref}",
        statement="Observed halt.",
        path=f"{ref}.c",
        line_number=2,
        content_sha256=f"hash-{ref}",
        commit_sha="commit-1",
        contributor_ref=None,
        attrs={"verifies": ref, "level": "system", "result": "pass"},
    )


def test_ac11_ac12_ac19_gate_blocks_and_keeps_gaps(tmp_path: Path):
    db = tmp_path / "store.sqlite"
    root = tmp_path / "src"
    root.mkdir()
    (root / "missing.c").write_text(
        "# REQ-1: The unit shall log a fault. [class=C]\n",
        encoding="utf-8",
    )
    assert main(["--db", str(db), "scan", str(root), "--tenant", "acme", "--project", "pump", "--class", "C"]) == 0
    out = tmp_path / "draft.md"
    assert main(["--db", str(db), "export", "--tenant", "acme", "--project", "pump", "--out", str(out)]) == 2
    assert not out.exists()

    assert (
        main(
            [
                "--db",
                str(db),
                "approve",
                "--tenant",
                "acme",
                "--project",
                "pump",
                "--name",
                "A. Quinn",
                "--role",
                "RA/QA",
                "--meaning",
                "approve_draft",
            ]
        )
        == 0
    )
    assert main(["--db", str(db), "export", "--tenant", "acme", "--project", "pump", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert DISCLAIMER in text
    assert "architecture_missing" in text
    assert "NOT A CONFORMITY ASSESSMENT" in text
    assert stat.S_IMODE(out.stat().st_mode) == 0o600

    assert (
        main(
            [
                "--db",
                str(db),
                "approve",
                "--tenant",
                "acme",
                "--project",
                "pump",
                "--name",
                "A. Quinn",
                "--role",
                "RA/QA",
                "--meaning",
                "reject",
                "--reason",
                "Gaps are not ready for review.",
            ]
        )
        == 0
    )
    rejected = tmp_path / "rejected.md"
    assert main(["--db", str(db), "export", "--tenant", "acme", "--project", "pump", "--out", str(rejected)]) == 2
    assert not rejected.exists()


def test_ac13_content_change_stales_approval_and_asks_for_reverification(tmp_path: Path, capsys):
    db = tmp_path / "store.sqlite"
    root = tmp_path / "src"
    root.mkdir()
    source = root / "device.c"
    source.write_text(
        "\n".join(
            [
                "# HAZARD-1: Air reaches the line.",
                "# RISK-4: Air in the line. [hazard=HAZARD-1] [harm=embolus] [severity=serious] [probability=not_estimated] [ctrl=CTRL-9]",
                "# CTRL-9: Halt delivery. [implements=REQ-101] [effectiveness=reviewed by the software lead]",
                "# ARCH-1: Controller.",
                "# DESIGN-1: Halt unit.",
                "# REQ-101: Halt when air is detected. [class=B] [arch=ARCH-1] [design=DESIGN-1]",
                "# TEST-1: System halt. [verifies=REQ-101] [level=system] [result=pass]",
                "# TEST-2: Unit halt. [verifies=REQ-101] [level=unit] [result=pass]",
                "# TEST-3: Integrated halt. [verifies=REQ-101] [level=integration] [result=pass]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assert main(["--db", str(db), "scan", str(root), "--tenant", "acme", "--project", "pump", "--class", "B"]) == 0
    assert (
        main(
            [
                "--db",
                str(db),
                "approve",
                "--tenant",
                "acme",
                "--project",
                "pump",
                "--name",
                "A. Quinn",
                "--role",
                "RA/QA",
                "--meaning",
                "approve_draft",
            ]
        )
        == 0
    )
    out = tmp_path / "draft.md"
    assert main(["--db", str(db), "export", "--tenant", "acme", "--project", "pump", "--out", str(out)]) == 0
    assert "No implementation drift detected" in out.read_text(encoding="utf-8")

    source.write_text(source.read_text(encoding="utf-8") + "/* calibration note */\n", encoding="utf-8")
    assert main(["--db", str(db), "scan", str(root), "--tenant", "acme", "--project", "pump", "--class", "B"]) == 0
    capsys.readouterr()
    stale = tmp_path / "stale.md"
    assert main(["--db", str(db), "export", "--tenant", "acme", "--project", "pump", "--out", str(stale)]) == 2
    captured = capsys.readouterr()
    assert "approval_stale" in captured.err
    assert "CTRL-9: reverification_required" in captured.err
    assert not stale.exists()

    assert (
        main(
            [
                "--db",
                str(db),
                "approve",
                "--tenant",
                "acme",
                "--project",
                "pump",
                "--name",
                "A. Quinn",
                "--role",
                "RA/QA",
                "--meaning",
                "approve_draft",
            ]
        )
        == 0
    )
    again = tmp_path / "again.md"
    assert main(["--db", str(db), "export", "--tenant", "acme", "--project", "pump", "--out", str(again)]) == 0
    assert "No implementation drift detected" in again.read_text(encoding="utf-8")


def test_ac14_free_tier_contributor_cap(tmp_path: Path):
    db = tmp_path / "store.sqlite"
    store = Store(db)
    store.ensure_tenant("acme", "Acme", "free")
    project_id = store.ensure_project("acme", "pump", "A")
    annotations = []
    for index in range(3):
        ref = f"REQ-{index}"
        annotations.append(_annotation(ref, f"ref-{index}", index + 1))
        annotations.append(_test_for(ref))
    store.replace_scan("acme", project_id, annotations, [])
    record_gate(store, "acme", "pump", signer_name="A. Quinn", role="RA/QA", meaning="approve_draft", reason="")
    assert decide_export(store, "acme", "pump").allowed

    annotations.append(_annotation("REQ-9", "ref-9", 9))
    annotations.append(_test_for("REQ-9"))
    store.replace_scan("acme", project_id, annotations, [])
    blocked = decide_export(store, "acme", "pump")
    assert blocked.allowed is False
    assert "free_tier_contributor_limit" in blocked.reasons
    store.close()

    team = Store(tmp_path / "team.sqlite")
    team.ensure_tenant("wide", "Wide", "team")
    team_project = team.ensure_project("wide", "pump", "A")
    team.replace_scan("wide", team_project, annotations, [])
    record_gate(team, "wide", "pump", signer_name="A. Quinn", role="RA/QA", meaning="approve_draft", reason="")
    assert decide_export(team, "wide", "pump").allowed
    team.close()


def test_ac15_ac16_ac21_isolation_access_erasure_and_file_mode(tmp_path: Path):
    db = tmp_path / "store.sqlite"
    store = Store(db)
    assert stat.S_IMODE(db.stat().st_mode) == 0o600
    store.ensure_tenant("alpha", "Alpha")
    store.ensure_tenant("beta", "Beta")
    alpha_project = store.ensure_project("alpha", "pump", "A")
    beta_project = store.ensure_project("beta", "other", "A")
    store.replace_scan(
        "alpha",
        alpha_project,
        [_annotation("REQ-1", "alpha-ref", 1), _test_for("REQ-1")],
        [],
    )
    store.replace_scan("beta", beta_project, [_annotation("REQ-9", "beta-ref", 1)], [])
    assert store.list_annotations("beta", alpha_project) == []
    assert {item.ref_id for item in store.list_annotations("alpha", alpha_project)} == {"REQ-1", "TEST-REQ-1"}

    record_gate(
        store,
        "alpha",
        "pump",
        signer_name="QuinlanZedstoneApprover",
        role="RA/QA",
        meaning="approve_draft",
        reason="",
    )
    exported = store.access_export("alpha")
    encoded = json.dumps(exported)
    assert "salt" not in exported["tenant"]
    assert "salt" not in encoded
    assert "contributor.one@example.com" not in encoded
    assert exported["approvals"][0]["signer_name"] == "QuinlanZedstoneApprover"
    assert "Git history was not included" in exported["note"]

    message = store.erase_tenant("alpha")
    assert message == ERASURE_LIMIT
    assert "not modified" in message
    store.close()
    raw = db.read_bytes()
    assert b"QuinlanZedstoneApprover" not in raw
    assert b"alpha-ref" not in raw

    reopened = Store(db)
    try:
        reopened.get_tenant("alpha")
        raised = False
    except Exception as exc:
        raised = True
        assert "alpha" in str(exc)
    assert raised
    assert reopened.get_tenant("beta")["name"] == "Beta"
    reopened.close()


def test_ac17_rule11_keeps_the_human_class(tmp_path: Path):
    matched = assess_rule11(
        limb="diagnostic_therapeutic",
        impact="death_or_irreversible",
        stated_class="III",
        also_considered_rules=["11"],
    )
    assert matched["binding"] is False
    assert matched["differs_from_stated_class"] is False
    assert "not a classification" in matched["notice"]
    assert matched["strictest_rule_note"] is None

    mismatched = assess_rule11(
        limb="diagnostic_therapeutic",
        impact="death_or_irreversible",
        stated_class="IIa",
        also_considered_rules=["11", "3.3"],
    )
    assert mismatched["stated_class"] == "IIa"
    assert mismatched["sentence_class"] == "III"
    assert mismatched["differs_from_stated_class"] is True
    assert "does not choose the strictest" in mismatched["strictest_rule_note"]

    unmatched = assess_rule11(
        limb="physiological_monitoring",
        impact="death_or_irreversible",
        stated_class="IIb",
    )
    assert unmatched["sentence_class"] is None
    assert unmatched["stated_class"] == "IIb"
    assert unmatched["differs_from_stated_class"] is True

    db = tmp_path / "store.sqlite"
    root = tmp_path / "src"
    root.mkdir()
    (root / "mod.c").write_text("# REQ-1: Halt. [class=A]\n", encoding="utf-8")
    assert main(["--db", str(db), "scan", str(root), "--tenant", "acme", "--project", "pump", "--class", "A"]) == 0
    assert (
        main(
            [
                "--db",
                str(db),
                "rule11",
                "--tenant",
                "acme",
                "--project",
                "pump",
                "--limb",
                "other",
                "--impact",
                "none",
                "--stated-class",
                "I",
                "--rules",
                "11",
            ]
        )
        == 0
    )


def test_reject_requires_a_reason_and_email_signer_is_refused(tmp_path: Path):
    db = tmp_path / "store.sqlite"
    root = tmp_path / "src"
    root.mkdir()
    (root / "mod.c").write_text("# REQ-1: Halt. [class=A]\n", encoding="utf-8")
    main(["--db", str(db), "scan", str(root), "--tenant", "acme", "--project", "pump", "--class", "A"])
    assert (
        main(
            [
                "--db",
                str(db),
                "approve",
                "--tenant",
                "acme",
                "--project",
                "pump",
                "--name",
                "A. Quinn",
                "--role",
                "RA/QA",
                "--meaning",
                "reject",
                "--reason",
                "no",
            ]
        )
        == 3
    )
    assert (
        main(
            [
                "--db",
                str(db),
                "approve",
                "--tenant",
                "acme",
                "--project",
                "pump",
                "--name",
                "quinn@example.com",
                "--role",
                "RA/QA",
                "--meaning",
                "approve_draft",
            ]
        )
        == 3
    )


def test_erase_command_refuses_a_mismatched_confirm(tmp_path: Path):
    db = tmp_path / "store.sqlite"
    store = Store(db)
    store.ensure_tenant("acme", "Acme")
    store.close()
    assert main(["--db", str(db), "erase", "--tenant", "acme", "--confirm", "nope"]) == 3
    assert main(["--db", str(db), "erase", "--tenant", "acme", "--confirm", "acme"]) == 0
    assert main(["--db", str(db), "access", "--tenant", "acme", "--out", str(tmp_path / "access.json")]) == 3
