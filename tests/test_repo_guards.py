# SPDX-License-Identifier: MIT
import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "documdr"

FORBIDDEN_MODULES = {
    "urllib",
    "http",
    "httpx",
    "requests",
    "aiohttp",
    "socket",
    "ftplib",
    "smtplib",
}


def test_ac18_library_has_no_network_client_and_no_shell():
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                names = []
            assert not (set(names) & FORBIDDEN_MODULES), path.name
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if (
                        keyword.arg == "shell"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is True
                    ):
                        raise AssertionError(f"shell=True in {path.name}")


def test_shell_true_text_is_absent():
    for path in SRC.rglob("*.py"):
        assert "shell=True" not in path.read_text(encoding="utf-8")


def test_ac20_gitignore_blocks_secrets_and_keeps_env_example():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (
        ".env",
        "*.pem",
        "*.key",
        "*.sqlite",
        ".documdr/",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "service-account",
        "*.dcm",
        "phi/",
        "patient-data/",
        ".aws/",
        "terraform.tfstate",
        "*.kdbx",
        ".npmrc",
        ".pypirc",
        "node_modules/",
        "__pycache__/",
        "*.log",
        "docker-compose.override.yml",
        "*.pfx",
    ):
        assert pattern in text
    ignored = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=ROOT, check=False)
    example = subprocess.run(["git", "check-ignore", "-q", ".env.example"], cwd=ROOT, check=False)
    assert ignored.returncode == 0
    assert example.returncode == 1
    example_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "ghp_" not in example_text
    assert "sk_live_" not in example_text
    assert "BEGIN PRIVATE KEY" not in example_text


def test_example_annotations_scan_as_class_a():
    from documdr.matrix import build_matrix
    from documdr.scan import scan_tree

    result = scan_tree(ROOT / "examples", b"example-salt")
    matrix = build_matrix(result.annotations, result.exclusions, "A")
    row = next(item for item in matrix.rows if item.requirement_id == "REQ-101")
    assert "Patient" not in row.statement
    assert "system_test_missing" not in row.gaps
    assert "architecture" in row.not_applicable
    assert row.system_tests == ["TEST-501"]
