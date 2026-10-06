# Spec 001 — Local IEC 62304 traceability engine

Status: accepted for the first implementation increment.

Parents: `specs/constitution.md`.

## Problem

Early SaMD teams annotate work in git and then retype it into a technical file. This increment compiles those annotations into a draft traceability matrix, a draft risk record, and a non-binding Rule 11 note, on the customer's machine, with a human approval gate in front of export.

## Users

A software engineer annotates code. A person the customer regards as responsible for quality or regulatory review approves or rejects the draft. DocuMDR does not decide whether that person is qualified.

## Non-goals

- GitHub, GitLab, Bitbucket, Jira, or Linear OAuth, webhooks, or marketplace listings.
- Accounts, billing, the €249 / €799 tiers' payment rails, and hosted multi-tenant SaaS. Local tenancy is in scope; cloud processing is not.
- EU MDR Annex II GSPR checklist builder, Annex III PMS, and EU AI Act Annex IV assembly. Those are later specs. This increment names them only as future work.
- FDA 510(k) documentation.
- Notified Body or EUDAMED submission.
- Automatic Article 73 or MDR vigilance reports.
- eIDAS qualified electronic signatures.
- Any claim that an export is audit-pass guaranteed.

## Regulatory decisions encoded here

These are product rules for a draft compiler. They are not a conformity opinion.

1. **IEC 62304:2006+AMD1:2015 class scaling.** Public descriptions of the 2006 edition omit system testing for Class A. AMD1 Table A.1 brings software system testing (clause 5.7), including requirement-to-test traceability, into Class A, B, and C. This spec follows AMD1. Sources and the residual uncertainty (the base clauses AMD1 did not restate were not purchased) are in `plan.md`.
2. **Class A row.** Required: requirement statement, implementation path, a system-level test that verifies the requirement and has a human `pass` result. Not applicable, and therefore not gaps: architecture, unit subdivision, detailed design, unit verification, integration testing. A missing git commit is a gap (`commit_identity_missing`) because configuration identity is otherwise incomplete.
3. **Class B row.** Adds architecture, unit subdivision (`design` id), unit verification, and integration testing. Detailed design narrative remains not applicable.
4. **Class C row.** Adds a non-empty detailed-design statement on the linked `DESIGN` item. Unit verification and integration testing are both required.
5. **Item class.** A requirement may set `[class=A|B|C]`. Evidence uses that class. If it is lower than the project class and `[class_rationale=...]` is empty, the row gap is `lower_class_needs_rationale`. An invalid class value does not invent a class: evidence falls back to the project class and the row records `safety_class_invalid`.
6. **ISO 14971 fields are human.** The engine never writes a default severity or probability. `probability=not_estimated` is the only automatic interpretation, and only because the person typed that token (ISO 14971 allows a plan for the case where probability cannot be estimated). There is no `acceptable` status.
7. **Two different verifications.** A passing test does not close risk-control effectiveness. Effectiveness is present only when the control carries a non-empty `[effectiveness=...]` value written by a person. Verification of implementation is a content-hash snapshot taken at `approve_draft`, compared on the next scan. Drift is reported as `reverification_required` and also makes the approval stale, because the hash sits inside the fingerprinted matrix.
8. **Rule 11.** The person states a limb, an impact, a class, and any other Annex VIII rules they considered. The engine quotes the matching Rule 11 sentence where one sentence matches, flags a mismatch, and does not replace the stated class. Several rules produce a reminder that Annex VIII rule 3.5 says the strictest applicable rule wins. The engine does not choose a winner.
9. **SOUP.** A `SOUP` item needs `title` and `designator` in every class. Class B and C also need `environment`. Missing fields are project gaps. A whole device software system is not recorded as SOUP by this tool.

## Tag grammar

One annotation per line. The id is `KIND-TOKEN` where `KIND` is `REQ`, `RISK`, `TEST`, `ARCH`, `DESIGN`, `SOUP`, `HAZARD`, `CTRL`, or `NEED`, and `TOKEN` is 1–32 letters or digits. The statement is the text after the id, up to the first `[`, with a leading colon or dash removed, collapsed whitespace, and a 500-character cap. Attributes are `[key=value]` or `[key]`. Keys are lowercase identifiers. Unknown keys are ignored. Email-shaped text in a statement or attribute is replaced with `[redacted-email]` before storage.

| Attribute | Used on | Meaning |
| --- | --- | --- |
| `class` | `REQ` | Item safety class `A`, `B`, or `C` |
| `class_rationale` | `REQ` | Required text when the item class is lower than the project class |
| `need` | `REQ` | `NEED-...` id |
| `arch` | `REQ` | `ARCH-...` id |
| `design` | `REQ` | `DESIGN-...` id |
| `risk` | `REQ` | Comma-separated `RISK-...` ids |
| `verifies` | `TEST` | Comma-separated `REQ-...` ids |
| `level` | `TEST` | `unit`, `integration`, or `system` |
| `result` | `TEST` | Human result `pass`, `fail`, or `not_run` |
| `hazard` | `RISK` | `HAZARD-...` id |
| `harm` | `RISK` | Short human description of harm |
| `severity` | `RISK` | Human estimate, stored exactly |
| `probability` | `RISK` | Human estimate, or exactly `not_estimated` |
| `ctrl` | `RISK` | Comma-separated `CTRL-...` ids |
| `implements` | `CTRL` | Comma-separated `REQ-...` ids |
| `effectiveness` | `CTRL` | Human pointer that effectiveness was considered |
| `title`, `designator`, `environment` | `SOUP` | SOUP identity and, for class B/C, the environment |

Duplicate ids are all stored. The matrix uses the annotation with the earliest `(path, line)` and adds project gap `duplicate_id:<id>`.

Illustrative line:

```text
# REQ-101: The compiler shall keep the requirement statement it was given. [class=A] [need=NEED-1]
```

## Scan rules

The scan root is a directory the user passes. The walk does not follow directory symlinks. A symlink whose target resolves outside the root is excluded as `symlink_escape` and is not read.

Excluded before reading, reason stored, content not stored:

- Any path segment named `.git`, `.venv`, `venv`, `node_modules`, `__pycache__`, `.documdr`, `phi`, `patient`, `patients`, `dicom`, `fhir`, `hl7`, `clinical-data`, `ehr`, or `patient-data`.
- File names `.env`, `.env.*` other than a literal negation (all dotenv files are excluded), `id_rsa`, `id_ed25519`, `credentials.json`, and `service-account.json`, plus suffixes `.pem`, `.key`, `.p12`, `.pfx`, `.kdbx`, `.dcm`, `.dicom`, `.hl7`, `.edf`, `.nii`, `.nii.gz`, `.sqlite`, `.sqlite3`, `.db`.

Excluded after a bounded read:

- Larger than `max_bytes` (default 1_000_000) or beyond `max_files` (default 5000).
- A NUL byte in the first 8 KiB (`binary`).
- Clinical payload: `MSH|` near the start of the file, or a JSON `"resourceType"` together with `"Patient"`, `"Observation"`, `"Condition"`, or `"DiagnosticReport"`. The word "Patient" alone does not match.

A line matching a secret pattern (assignment to api key, secret, password, token, or private key; a PEM private-key banner; or common token prefixes `ghp_`, `github_pat_`, `glpat-`, `AKIA`, `xox[baprs]-`, `sk_live_`) produces exclusion `secret_redacted` with path and line number only. The line is not parsed and its text is not stored.

For each kept annotation the engine stores the relative POSIX path, line number, SHA-256 of the whole file, the current file's last commit from local `git log -1` when git is available, and `HMAC-SHA256(tenant_salt, lowercased email)` truncated to 32 hex characters. The email and the author name are discarded. No network call is made.

## Matrix and fingerprint

`build_matrix` returns requirement rows, risk records, project gaps, and exclusions. The fingerprint is SHA-256 of the canonical JSON (`sort_keys`, compact separators) of that structure. Implementation-change notes are not part of the fingerprint. File content hashes are.

Requirement gap codes:

`requirement_statement_missing`, `safety_class_invalid`, `lower_class_needs_rationale`, `malformed_link`, `system_test_missing`, `system_test_result_missing`, `system_test_failed`, `architecture_missing`, `architecture_undefined`, `design_missing`, `design_undefined`, `detailed_design_missing`, `unit_verification_missing`, `integration_test_missing`, `test_level_unrecognised`, `commit_identity_missing`.

Not-applicable codes, which must not also appear as gaps: `architecture`, `design`, `detailed_design`, `unit_verification`, `integration_test`.

Risk gap codes when a `RISK` annotation exists (any project class, because the person opened an ISO 14971 record): `hazard_missing`, `harm_missing`, `severity_not_estimated`, `probability_missing`, `risk_control_missing`, `verification_of_effectiveness_missing`, `orphan_control` (a `CTRL` that no risk lists; project gap).

Project gap `software_risk_process_missing` applies only to class B and C projects that contain no `RISK` annotation.

A system test closes `system_test_missing` only when `level=system`, `verifies` contains the requirement, and `result=pass`. `fail` yields `system_test_failed`. `not_run` or any other result yields `system_test_result_missing`. The same pattern applies to unit and integration levels.

## Approval, export, and drift

`approve_draft` and `reject` each record signer name (at least two characters, must not be an email address), role (at least two characters), UTC timestamp, matrix fingerprint, and a control snapshot `{control id: {requirement id: content sha}}`. `reject` requires a reason of at least three characters.

Export writes a file only when all of the following hold:

- The latest gate for the project is `approve_draft`.
- That gate's fingerprint equals the current matrix fingerprint.
- The latest gate is not `reject`.
- A `free` plan tenant has at most three distinct contributor refs on the project. The `team` plan does not apply this cap. The cap is the free-tier seat rule from the venture brief, enforced locally.

Otherwise export writes nothing and returns one or more of: `approval_missing`, `approval_rejected`, `approval_stale`, `free_tier_contributor_limit`.

Change notes, shown even when export is blocked:

- No prior `approve_draft` snapshot and the risk has a control: `verification_of_implementation_missing`.
- Snapshot content hash differs from the current requirement hash: `reverification_required`.
- Snapshot matches: the allowed export says implementation drift was not detected.

The markdown draft starts with the standing disclaimer: the file is a draft, not a conformity assessment, not legal or regulatory advice, and not a Notified Body opinion. Known gaps remain visible after approval so the gate cannot launder them.

## Tenancy, access, and erasure

A tenant has an id, display name, plan (`free` or `team`), a random 32-byte salt, residency `eu_eea`, and a creation time. Projects belong to one tenant and carry the IEC 62304 project class plus an optional Rule 11 record. Every read and write is filtered by tenant id.

Access export (Article 15 support for the local store) returns the tenant profile without the salt, projects, contributor refs, approvals (names included, because they are the personal data held), exclusions (paths and reasons only), and annotation metadata. It must not contain raw emails or file bodies.

Erasure deletes the tenant's rows from the local database, including approver names, and reports that git history on disk was not deleted. A missing tenant raises `TenantNotFound`. The database file mode is `0600` and its directory, when created by the CLI, is `0700`. Draft and access files are written as `0600`.

Audit rows record an action name, tenant id, optional project id, optional object id, and a timestamp. They do not record statements, paths, or names.

## Acceptance criteria

- AC-01 Tag grammar parses kinds, statements, and attributes, and redacts emails inside statements.
- AC-02 Secret-bearing lines are not stored; path and line may be.
- AC-03 Clinical directories, clinical extensions, and FHIR/HL7 payloads are not stored.
- AC-04 The word "Patient" in an ordinary requirement is kept.
- AC-05 Contributor emails and author names are absent from the database; a pseudonymous ref is kept.
- AC-06 Class A marks architecture, design, unit verification, and integration as not applicable, and still gaps a missing system test.
- AC-07 Class B requires architecture, design id, unit verification, integration, and system test, and marks detailed design not applicable.
- AC-08 Class C gaps an empty detailed design as well as missing unit and integration tests.
- AC-09 Severity and probability stay null until a human supplies them; `not_estimated` is stored only when written by the person.
- AC-10 A passing test does not remove `verification_of_effectiveness_missing`.
- AC-11 Export is blocked with `approval_missing` until `approve_draft`.
- AC-12 A later `reject` blocks export with `approval_rejected` and writes no file.
- AC-13 After approval, editing an implemented file yields `approval_stale` and `reverification_required`.
- AC-14 The free plan blocks export when a fourth distinct contributor ref appears. Three refs do not.
- AC-15 A second tenant cannot read the first tenant's annotations, even with the project id.
- AC-16 Access export omits the salt and the raw email. Erasure removes the approver name and does not claim git history was deleted.
- AC-17 Rule 11 keeps a mismatched stated class, sets a non-binding notice, and does not invent a class when no single sentence matches.
- AC-18 The `src/documdr` library does not import a network client and does not set `shell=True`.
- AC-19 An allowed export contains the conformity disclaimer and still lists open gaps.
- AC-20 The gitignore covers secrets, clinical artefacts, and local stores, and does not ignore `.env.example`.
- AC-21 The SQLite file is mode `0600` on POSIX.
- AC-22 A lower item class without a rationale is gap `lower_class_needs_rationale`.
- AC-23 Duplicate ids keep the earliest path and line, and record `duplicate_id`.
- AC-24 A symlink that resolves outside the root is not read.
