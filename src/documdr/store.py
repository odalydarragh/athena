# SPDX-License-Identifier: MIT
"""Tenant-scoped SQLite store. The salt never leaves this module except as an HMAC input."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from documdr.disclaimer import ERASURE_LIMIT
from documdr.errors import ProjectNotFound, TenantNotFound
from documdr.models import Annotation, Exclusion

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    plan TEXT NOT NULL CHECK (plan IN ('free', 'team')),
    salt BLOB NOT NULL,
    residency TEXT NOT NULL CHECK (residency = 'eu_eea'),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    iec62304_class TEXT NOT NULL CHECK (iec62304_class IN ('A', 'B', 'C')),
    rule11_json TEXT,
    UNIQUE (tenant_id, name)
);
CREATE TABLE IF NOT EXISTS annotations (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    statement TEXT NOT NULL,
    path TEXT,
    line_number INTEGER,
    content_sha256 TEXT NOT NULL,
    commit_sha TEXT,
    contributor_ref TEXT,
    attrs_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exclusions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    path TEXT NOT NULL,
    reason TEXT NOT NULL,
    line_number INTEGER
);
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    signer_name TEXT NOT NULL,
    role TEXT NOT NULL,
    meaning TEXT NOT NULL CHECK (meaning IN ('approve_draft', 'reject')),
    reason TEXT NOT NULL DEFAULT '',
    matrix_fingerprint TEXT NOT NULL,
    control_snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    action TEXT NOT NULL,
    project_id TEXT,
    object_id TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_annotations_tenant ON annotations (tenant_id, project_id);
CREATE INDEX IF NOT EXISTS idx_exclusions_tenant ON exclusions (tenant_id, project_id);
CREATE INDEX IF NOT EXISTS idx_approvals_tenant ON approvals (tenant_id, project_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        parent_existed = path.parent.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not parent_existed:
            os.chmod(path.parent, 0o700)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA secure_delete = ON")
        self.conn.executescript(_SCHEMA)
        self.conn.commit()
        os.chmod(path, 0o600)

    def close(self) -> None:
        self.conn.close()

    def ensure_tenant(self, tenant_id: str, name: str, plan: str = "free") -> None:
        if plan not in {"free", "team"}:
            raise ValueError("plan must be free or team")
        row = self.conn.execute("SELECT id FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
        if row is not None:
            return
        self.conn.execute(
            "INSERT INTO tenants (id, name, plan, salt, residency, created_at) VALUES (?, ?, ?, ?, 'eu_eea', ?)",
            (tenant_id, name, plan, secrets.token_bytes(32), _now()),
        )
        self._audit(tenant_id, "tenant_created", None, None)
        self.conn.commit()

    def get_tenant(self, tenant_id: str) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
        if row is None:
            raise TenantNotFound(f"no tenant {tenant_id}")
        return row

    def salt_for(self, tenant_id: str) -> bytes:
        return bytes(self.get_tenant(tenant_id)["salt"])

    def ensure_project(self, tenant_id: str, name: str, iec62304_class: str) -> str:
        self.get_tenant(tenant_id)
        if iec62304_class not in {"A", "B", "C"}:
            raise ValueError("IEC 62304 class must be A, B, or C")
        row = self.conn.execute(
            "SELECT id FROM projects WHERE tenant_id = ? AND name = ?",
            (tenant_id, name),
        ).fetchone()
        if row is None:
            project_id = str(uuid.uuid4())
            self.conn.execute(
                "INSERT INTO projects (id, tenant_id, name, iec62304_class, rule11_json) VALUES (?, ?, ?, ?, NULL)",
                (project_id, tenant_id, name, iec62304_class),
            )
        else:
            project_id = row["id"]
            self.conn.execute(
                "UPDATE projects SET iec62304_class = ? WHERE id = ? AND tenant_id = ?",
                (iec62304_class, project_id, tenant_id),
            )
        self.conn.commit()
        return project_id

    def project_by_name(self, tenant_id: str, name: str) -> sqlite3.Row:
        self.get_tenant(tenant_id)
        row = self.conn.execute(
            "SELECT * FROM projects WHERE tenant_id = ? AND name = ?",
            (tenant_id, name),
        ).fetchone()
        if row is None:
            raise ProjectNotFound(f"no project {name}")
        return row

    def set_rule11(self, tenant_id: str, project_id: str, record: dict) -> None:
        if record.get("binding") is not False:
            raise ValueError("rule 11 record must be non-binding")
        self._owned_project(tenant_id, project_id)
        self.conn.execute(
            "UPDATE projects SET rule11_json = ? WHERE id = ? AND tenant_id = ?",
            (json.dumps(record, sort_keys=True), project_id, tenant_id),
        )
        self.conn.commit()

    def replace_scan(
        self,
        tenant_id: str,
        project_id: str,
        annotations: list[Annotation],
        exclusions: list[Exclusion],
    ) -> None:
        self._owned_project(tenant_id, project_id)
        with self.conn:
            self.conn.execute(
                "DELETE FROM annotations WHERE tenant_id = ? AND project_id = ?",
                (tenant_id, project_id),
            )
            self.conn.execute(
                "DELETE FROM exclusions WHERE tenant_id = ? AND project_id = ?",
                (tenant_id, project_id),
            )
            for annotation in annotations:
                self.conn.execute(
                    """
                    INSERT INTO annotations (
                        id, tenant_id, project_id, kind, ref_id, statement, path, line_number,
                        content_sha256, commit_sha, contributor_ref, attrs_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        tenant_id,
                        project_id,
                        annotation.kind,
                        annotation.ref_id,
                        annotation.statement,
                        annotation.path,
                        annotation.line_number,
                        annotation.content_sha256,
                        annotation.commit_sha,
                        annotation.contributor_ref,
                        json.dumps(annotation.attrs, sort_keys=True),
                    ),
                )
            for exclusion in exclusions:
                self.conn.execute(
                    """
                    INSERT INTO exclusions (id, tenant_id, project_id, path, reason, line_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        tenant_id,
                        project_id,
                        exclusion.path,
                        exclusion.reason,
                        exclusion.line_number,
                    ),
                )
            self._audit(tenant_id, "project_scanned", project_id, None)

    def list_annotations(self, tenant_id: str, project_id: str) -> list[Annotation]:
        rows = self.conn.execute(
            """
            SELECT * FROM annotations
            WHERE tenant_id = ? AND project_id = ?
            ORDER BY path, line_number, ref_id
            """,
            (tenant_id, project_id),
        ).fetchall()
        return [
            Annotation(
                kind=row["kind"],
                ref_id=row["ref_id"],
                statement=row["statement"],
                path=row["path"] or "",
                line_number=row["line_number"] or 0,
                content_sha256=row["content_sha256"],
                commit_sha=row["commit_sha"],
                contributor_ref=row["contributor_ref"],
                attrs=json.loads(row["attrs_json"]),
            )
            for row in rows
        ]

    def list_exclusions(self, tenant_id: str, project_id: str) -> list[Exclusion]:
        rows = self.conn.execute(
            "SELECT * FROM exclusions WHERE tenant_id = ? AND project_id = ?",
            (tenant_id, project_id),
        ).fetchall()
        return [
            Exclusion(path=row["path"], reason=row["reason"], line_number=row["line_number"])
            for row in rows
        ]

    def contributor_count(self, tenant_id: str, project_id: str) -> int:
        row = self.conn.execute(
            """
            SELECT COUNT(DISTINCT contributor_ref) AS seats
            FROM annotations
            WHERE tenant_id = ? AND project_id = ?
              AND contributor_ref IS NOT NULL AND contributor_ref != ''
            """,
            (tenant_id, project_id),
        ).fetchone()
        return int(row["seats"])

    def add_approval(
        self,
        tenant_id: str,
        project_id: str,
        *,
        signer_name: str,
        role: str,
        meaning: str,
        reason: str,
        matrix_fingerprint: str,
        control_snapshot: dict,
    ) -> str:
        self._owned_project(tenant_id, project_id)
        if meaning not in {"approve_draft", "reject"}:
            raise ValueError("meaning must be approve_draft or reject")
        if "@" in signer_name or len(signer_name.strip()) < 2:
            raise ValueError("signer name must be at least two characters and must not be an email")
        if len(role.strip()) < 2:
            raise ValueError("role must be at least two characters")
        if meaning == "reject" and len(reason.strip()) < 3:
            raise ValueError("a rejection needs a reason")
        approval_id = str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO approvals (
                id, tenant_id, project_id, signer_name, role, meaning, reason,
                matrix_fingerprint, control_snapshot_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval_id,
                tenant_id,
                project_id,
                signer_name.strip(),
                role.strip(),
                meaning,
                reason.strip(),
                matrix_fingerprint,
                json.dumps(control_snapshot, sort_keys=True),
                _now(),
            ),
        )
        self._audit(tenant_id, "approval_recorded", project_id, approval_id)
        self.conn.commit()
        return approval_id

    def latest_approval(self, tenant_id: str, project_id: str, meaning: str | None = None) -> sqlite3.Row | None:
        if meaning is None:
            return self.conn.execute(
                """
                SELECT * FROM approvals
                WHERE tenant_id = ? AND project_id = ?
                ORDER BY rowid DESC LIMIT 1
                """,
                (tenant_id, project_id),
            ).fetchone()
        return self.conn.execute(
            """
            SELECT * FROM approvals
            WHERE tenant_id = ? AND project_id = ? AND meaning = ?
            ORDER BY rowid DESC LIMIT 1
            """,
            (tenant_id, project_id, meaning),
        ).fetchone()

    def record_export(self, tenant_id: str, project_id: str, fingerprint: str) -> None:
        self._audit(tenant_id, "export_rendered", project_id, fingerprint)
        self.conn.commit()

    def access_export(self, tenant_id: str) -> dict:
        tenant = self.get_tenant(tenant_id)
        projects = self.conn.execute(
            "SELECT id, name, iec62304_class, rule11_json FROM projects WHERE tenant_id = ?",
            (tenant_id,),
        ).fetchall()
        refs = self.conn.execute(
            """
            SELECT DISTINCT contributor_ref FROM annotations
            WHERE tenant_id = ? AND contributor_ref IS NOT NULL
            ORDER BY contributor_ref
            """,
            (tenant_id,),
        ).fetchall()
        approvals = self.conn.execute(
            """
            SELECT signer_name, role, meaning, reason, matrix_fingerprint, created_at
            FROM approvals WHERE tenant_id = ? ORDER BY rowid
            """,
            (tenant_id,),
        ).fetchall()
        annotations = self.conn.execute(
            """
            SELECT ref_id, kind, statement, path, line_number, contributor_ref, commit_sha, content_sha256
            FROM annotations WHERE tenant_id = ? ORDER BY path, line_number
            """,
            (tenant_id,),
        ).fetchall()
        exclusions = self.conn.execute(
            "SELECT path, reason, line_number FROM exclusions WHERE tenant_id = ?",
            (tenant_id,),
        ).fetchall()
        self._audit(tenant_id, "access_exported", None, None)
        self.conn.commit()
        return {
            "note": (
                "This copy lists personal data held in the local DocuMDR store. "
                "Raw contributor emails are not held. Git history was not included and was not modified."
            ),
            "tenant": {
                "id": tenant["id"],
                "name": tenant["name"],
                "plan": tenant["plan"],
                "residency": tenant["residency"],
                "created_at": tenant["created_at"],
            },
            "projects": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "iec62304_class": row["iec62304_class"],
                    "rule11": json.loads(row["rule11_json"]) if row["rule11_json"] else None,
                }
                for row in projects
            ],
            "contributor_refs": [row["contributor_ref"] for row in refs],
            "approvals": [dict(row) for row in approvals],
            "annotations": [dict(row) for row in annotations],
            "exclusions": [dict(row) for row in exclusions],
        }

    def erase_tenant(self, tenant_id: str) -> str:
        self.get_tenant(tenant_id)
        with self.conn:
            for statement in (
                "DELETE FROM audit WHERE tenant_id = ?",
                "DELETE FROM approvals WHERE tenant_id = ?",
                "DELETE FROM exclusions WHERE tenant_id = ?",
                "DELETE FROM annotations WHERE tenant_id = ?",
                "DELETE FROM projects WHERE tenant_id = ?",
                "DELETE FROM tenants WHERE id = ?",
            ):
                self.conn.execute(statement, (tenant_id,))
        self.conn.execute("VACUUM")
        return ERASURE_LIMIT

    def _owned_project(self, tenant_id: str, project_id: str) -> None:
        self.get_tenant(tenant_id)
        row = self.conn.execute(
            "SELECT id FROM projects WHERE id = ? AND tenant_id = ?",
            (project_id, tenant_id),
        ).fetchone()
        if row is None:
            raise ProjectNotFound(f"no project {project_id}")

    def _audit(self, tenant_id: str, action: str, project_id: str | None, object_id: str | None) -> None:
        self.conn.execute(
            "INSERT INTO audit (id, tenant_id, action, project_id, object_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), tenant_id, action, project_id, object_id, _now()),
        )
