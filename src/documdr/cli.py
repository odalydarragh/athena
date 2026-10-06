# SPDX-License-Identifier: MIT
"""Local command line. No network calls."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from documdr.disclaimer import DISCLAIMER
from documdr.errors import DocuMDRError
from documdr.export import decide_export, project_matrix, record_gate, write_export
from documdr.matrix import fingerprint
from documdr.rule11 import assess_rule11
from documdr.scan import scan_tree
from documdr.store import Store

DEFAULT_DB = Path(".documdr") / "store.sqlite"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="documdr",
        description="Draft IEC 62304 traceability records from local annotations.",
        epilog=DISCLAIMER,
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite path. Defaults to ./.documdr/store.sqlite")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a local directory into a tenant project")
    scan.add_argument("root", type=Path)
    scan.add_argument("--tenant", required=True)
    scan.add_argument("--project", required=True)
    scan.add_argument("--class", dest="iec_class", required=True, choices=("A", "B", "C"))
    scan.add_argument("--plan", choices=("free", "team"), default="free")
    scan.set_defaults(func=cmd_scan)

    rule = sub.add_parser("rule11", help="Record a non-binding Rule 11 note")
    rule.add_argument("--tenant", required=True)
    rule.add_argument("--project", required=True)
    rule.add_argument("--limb", required=True)
    rule.add_argument("--impact", required=True)
    rule.add_argument("--stated-class", required=True)
    rule.add_argument("--rules", nargs="*", default=[])
    rule.set_defaults(func=cmd_rule11)

    approve = sub.add_parser("approve", help="Record an approval gate for the current matrix")
    approve.add_argument("--tenant", required=True)
    approve.add_argument("--project", required=True)
    approve.add_argument("--name", required=True)
    approve.add_argument("--role", required=True)
    approve.add_argument("--meaning", required=True, choices=("approve_draft", "reject"))
    approve.add_argument("--reason", default="")
    approve.set_defaults(func=cmd_approve)

    export = sub.add_parser("export", help="Write a draft only when the gate allows it")
    export.add_argument("--tenant", required=True)
    export.add_argument("--project", required=True)
    export.add_argument("--out", type=Path, required=True)
    export.set_defaults(func=cmd_export)

    access = sub.add_parser("access", help="Write a copy of personal data held for a tenant")
    access.add_argument("--tenant", required=True)
    access.add_argument("--out", type=Path, required=True)
    access.set_defaults(func=cmd_access)

    erase = sub.add_parser("erase", help="Delete a tenant's local rows")
    erase.add_argument("--tenant", required=True)
    erase.add_argument("--confirm", required=True)
    erase.set_defaults(func=cmd_erase)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (DocuMDRError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 3


def cmd_scan(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not root.is_dir():
        raise ValueError("scan root must be a directory")
    store = Store(Path(args.db))
    try:
        store.ensure_tenant(args.tenant, args.tenant, args.plan)
        result = scan_tree(root, store.salt_for(args.tenant))
        project_id = store.ensure_project(args.tenant, args.project, args.iec_class)
        store.replace_scan(args.tenant, project_id, result.annotations, result.exclusions)
        matrix = project_matrix(store, args.tenant, args.project)[1]
        gap_count = sum(len(row.gaps) for row in matrix.rows) + sum(len(risk.gaps) for risk in matrix.risks)
        gap_count += len(matrix.project_gaps)
        print(
            f"annotations={len(result.annotations)} exclusions={len(result.exclusions)} "
            f"gaps={gap_count} fingerprint={fingerprint(matrix)}"
        )
    finally:
        store.close()
    return 0


def cmd_rule11(args: argparse.Namespace) -> int:
    store = Store(Path(args.db))
    try:
        project = store.project_by_name(args.tenant, args.project)
        record = assess_rule11(
            limb=args.limb,
            impact=args.impact,
            stated_class=args.stated_class,
            also_considered_rules=args.rules,
        )
        store.set_rule11(args.tenant, project["id"], record)
        print(record["notice"])
        print(f"stated_class={record['stated_class']} differs={record['differs_from_stated_class']}")
    finally:
        store.close()
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    store = Store(Path(args.db))
    try:
        approval_id = record_gate(
            store,
            args.tenant,
            args.project,
            signer_name=args.name,
            role=args.role,
            meaning=args.meaning,
            reason=args.reason,
        )
        print(f"approval={approval_id} meaning={args.meaning}")
    finally:
        store.close()
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    store = Store(Path(args.db))
    try:
        decision = decide_export(store, args.tenant, args.project)
        if not decision.allowed or decision.markdown is None:
            for reason in decision.reasons:
                print(reason, file=sys.stderr)
            for note in decision.change_notes:
                print(note, file=sys.stderr)
            return 2
        write_export(args.out, decision.markdown)
        project = store.project_by_name(args.tenant, args.project)
        store.record_export(args.tenant, project["id"], decision.fingerprint)
        print(f"wrote {args.out}")
    finally:
        store.close()
    return 0


def cmd_access(args: argparse.Namespace) -> int:
    store = Store(Path(args.db))
    try:
        payload = store.access_export(args.tenant)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(args.out, 0o600)
        print(f"wrote {args.out}")
    finally:
        store.close()
    return 0


def cmd_erase(args: argparse.Namespace) -> int:
    if args.confirm != args.tenant:
        raise ValueError("confirm must match the tenant id")
    store = Store(Path(args.db))
    try:
        print(store.erase_tenant(args.tenant))
    finally:
        store.close()
    return 0
