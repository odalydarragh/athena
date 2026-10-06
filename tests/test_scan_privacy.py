# SPDX-License-Identifier: MIT
import json
import subprocess
from pathlib import Path

from documdr.scan import scan_tree
from documdr.store import Store

SENTINEL = "ZZ-PATIENT-NAME-UNIQUE"
SECRET = "SUPERSECRETTOKENVALUE12345"
EMAIL = "contributor.one@example.com"
AUTHOR = "Pat Example"


def test_ac02_ac03_ac04_denylist_keeps_ordinary_source(tmp_path: Path):
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "ui.py").write_text(
        "# REQ-200: The UI shall show the word Patient in a label. [class=A]\n",
        encoding="utf-8",
    )
    (root / "src" / "fhir_client.py").write_text(
        "# REQ-201: The client shall call the labelled endpoint. [class=A]\n",
        encoding="utf-8",
    )
    (root / "src" / "module.py").write_text(
        f"api_key = {SECRET}\n# REQ-202: Halt on fault. [class=A]\n",
        encoding="utf-8",
    )
    (root / "image.dcm").write_text(SENTINEL, encoding="utf-8")
    (root / "bundle.json").write_text(
        json.dumps({"resourceType": "Patient", "name": [{"text": SENTINEL}]}),
        encoding="utf-8",
    )
    (root / "message.hl7").write_text(f"MSH|^~\\&|{SENTINEL}\n", encoding="utf-8")
    phi = root / "phi"
    phi.mkdir()
    (phi / "note.txt").write_text(f"# REQ-404: {SENTINEL}\n", encoding="utf-8")
    (root / ".env").write_text(f"GITHUB_TOKEN={SECRET}\n# REQ-405: ignored\n", encoding="utf-8")
    (root / "key.pem").write_bytes(b"-----BEGIN PRIVATE KEY-----\n" + SENTINEL.encode())

    result = scan_tree(root, b"salt-bytes-for-test-only")
    blob = json.dumps(
        [
            {
                "ref_id": item.ref_id,
                "statement": item.statement,
                "path": item.path,
                "attrs": item.attrs,
            }
            for item in result.annotations
        ]
    )
    assert "REQ-200" in blob
    assert "REQ-201" in blob
    assert "REQ-202" in blob
    assert "REQ-404" not in blob
    assert "REQ-405" not in blob
    assert SENTINEL not in blob
    assert SECRET not in blob
    reasons = {item.reason for item in result.exclusions}
    assert "clinical_extension" in reasons
    assert "clinical_payload" in reasons
    assert "secret_redacted" in reasons
    assert "secret_filename" in reasons
    assert "denied_directory" in reasons


def test_ac24_symlink_outside_root_is_not_read(tmp_path: Path):
    outside = tmp_path / "outside.txt"
    outside.write_text(f"# REQ-1: {SENTINEL}\n", encoding="utf-8")
    root = tmp_path / "repo"
    root.mkdir()
    (root / "link.txt").symlink_to(outside)
    result = scan_tree(root, b"salt")
    blob = json.dumps([item.statement for item in result.annotations])
    assert SENTINEL not in blob
    assert result.annotations == []
    assert any(item.reason == "symlink_escape" for item in result.exclusions)


def test_oversized_and_binary_files_are_not_stored(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "big.py").write_text("# REQ-1: " + ("x" * 50) + "\n", encoding="utf-8")
    (root / "bin.py").write_bytes(b"\x00# REQ-2: hidden\n")
    result = scan_tree(root, b"salt", max_bytes=20)
    assert result.annotations == []
    reasons = {item.reason for item in result.exclusions}
    assert reasons == {"file_too_large", "binary"}


def test_ac05_contributor_email_is_pseudonymised(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", EMAIL], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", AUTHOR], cwd=repo, check=True)
    (repo / "halt.c").write_text(
        "# REQ-101: The controller shall halt. [class=A]\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "halt.c"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "annotate"], cwd=repo, check=True, capture_output=True)

    store = Store(tmp_path / "store.sqlite")
    store.ensure_tenant("acme", "Acme")
    salt = store.salt_for("acme")
    result = scan_tree(repo, salt)
    project_id = store.ensure_project("acme", "pump", "A")
    store.replace_scan("acme", project_id, result.annotations, result.exclusions)
    store.close()

    raw = (tmp_path / "store.sqlite").read_bytes()
    assert EMAIL.encode() not in raw
    assert AUTHOR.encode() not in raw
    assert len(result.annotations) == 1
    assert result.annotations[0].contributor_ref
    assert result.annotations[0].contributor_ref != EMAIL
    assert result.annotations[0].commit_sha
