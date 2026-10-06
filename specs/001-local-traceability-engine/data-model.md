# Data model 001

Personal data is called out in the "Held about a person" column. Anything not listed there is not collected on purpose.

## Tenant

| Field | Held about a person | Notes |
| --- | --- | --- |
| `id` | No | Caller-chosen slug. |
| `name` | Only if the caller puts a person's name in it | Display label. Prefer an organisation name. |
| `plan` | No | `free` (3 contributor refs) or `team`. |
| `salt` | Secret, not personal data | 32 random bytes. HMAC key. Never exported. Deleted on erasure. |
| `residency` | No | Only `eu_eea` in this spec. |
| `created_at` | No | UTC ISO-8601. |

## Project

| Field | Notes |
| --- | --- |
| `id`, `tenant_id`, `name` | Unique name per tenant. |
| `iec62304_class` | `A`, `B`, or `C`. Project default. |
| `rule11_json` | Non-binding record from spec 001. `binding` must be false. |

## Annotation

One parsed tag. File bodies are not a field.

| Field | Held about a person | Notes |
| --- | --- | --- |
| `ref_id`, `kind`, `statement` | Statement might quote a person if the customer typed one | Statement capped at 500 characters. Emails redacted. |
| `path`, `line_number` | Path might contain a username if the customer uses one in a directory | Relative POSIX path. |
| `content_sha256` | No | Hash of the file bytes. |
| `commit_sha` | No | From local git, when available. |
| `contributor_ref` | Pseudonymous | First 32 hex chars of HMAC-SHA256(salt, lowercased email). Null when git has no email. |
| `attrs_json` | Same caveat as statement | Known attributes only, emails redacted. |

Author display names are not a field.

## Exclusion

`path`, `reason`, optional `line_number`. No excerpt. Reasons include `denied_directory`, `denied_file_type`, `secret_filename`, `clinical_extension`, `clinical_payload`, `secret_redacted`, `binary`, `file_too_large`, `scan_cap`, `symlink_escape`.

## Approval

| Field | Held about a person | Notes |
| --- | --- | --- |
| `signer_name`, `role` | Yes, because the gate requires a named person | Name must not be an email address. |
| `meaning` | No | `approve_draft` or `reject`. |
| `reason` | Maybe | Required for reject. |
| `matrix_fingerprint` | No | SHA-256 of canonical matrix JSON. |
| `control_snapshot_json` | No | Content hashes per control and requirement. |
| `created_at` | No | UTC. |

## Audit

`action`, `tenant_id`, optional `project_id`, optional `object_id`, `created_at`. No statements, paths, names, or emails. Actions: `tenant_created`, `project_scanned`, `approval_recorded`, `export_rendered`, `access_exported`, `tenant_erased`.

## Canonical matrix (fingerprinted)

```text
{
  project_class, project_gaps[], exclusions[{path, reason, line_number}],
  rows[{
    requirement_id, statement, safety_class, need_id, architecture_id, design_id,
    implementation_path, implementation_commit, implementation_content_sha256,
    system_tests[], unit_tests[], integration_tests[], risk_ids[],
    gaps[], not_applicable[]
  }],
  risks[{
    risk_id, statement, hazard_id, harm, severity, probability,
    probability_not_estimated, controls[{control_id, implements[], effectiveness}],
    gaps[]
  }]
}
```

Lists inside a record are sorted. Change-evaluation notes and the disclaimer are not fingerprinted. The content hash is.

## Erasure boundary

Deleting a tenant removes every row above for that tenant id, then removes the tenant. It does not modify git objects, working-tree files, or remotes. The access and erase commands say that in their output.
