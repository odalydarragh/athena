# Plan 001 — Local traceability engine

## Increment

Ship a stdlib Python package, `documdr`, that implements spec 001. No web server, no OAuth, no third-party runtime dependencies. Tests use pytest, which is a development dependency only.

```text
src/documdr/
  privacy.py     path, secret, and clinical denylist
  tags.py        grammar
  scan.py        local walk and git metadata
  matrix.py      class scaling, risks, fingerprint
  rule11.py      non-binding Rule 11 record
  store.py       tenant-scoped SQLite
  export.py      approval gate and markdown
  cli.py         scan, rule11, approve, export, access, erase
tests/           one module per acceptance cluster
examples/        synthetic Class A annotations, no personal data
```

The CLI is the only interface in this increment. Default database path: `./.documdr/store.sqlite`, which git ignores.

## Why these choices

- **Python stdlib.** The engine has to be readable by a regulatory reviewer and auditable for network calls. A framework would add supply-chain surface before there is a hosted product.
- **SQLite, not a hosted database.** Version 1 must not put repository metadata on a server. Tenant id is still a column on every table so a later cloud spec can reuse the isolation tests.
- **Content hashes instead of commit shas typed into source.** A sha written into the file changes the commit that contains it, so the comparison can never succeed. The fingerprint covers the file hash. The approval stores a snapshot of those hashes for the change note.
- **AMD1 class table.** MathWorks' public overview and the AMD1 summary table include system testing for Class A. Some 2026 secondary guides still describe the 2006 table, where Class A stops before system testing. The purchased base text of clauses AMD1 did not replace was not available. The spec follows the AMD1 movement of clause 5.7 to all classes and says so in the export.
- **Gaps do not block export.** Teams need a draft that shows what is missing. The constitution's human gate is what blocks a file from being written. An approved draft still prints its gaps.
- **Cloud OAuth is deferred.** The venture roadmap asks for GitHub and GitLab webhooks. Doing that now would require client secrets and a processor role. Both are forbidden by the constitution until a data-processing agreement and an EU hosting decision exist. The local parser is the part that removes regulatory retyping without taking source code off the machine.

## Later specs (not this increment)

- 002 — Annex II section index and GSPR cross-references, still local, still draft.
- 003 — EU AI Act Annex IV headings as an empty controlled template. No model training logs are ingested until a data-governance spec says what is minimised.
- 004 — Cloud processor mode: Art. 28 terms, subprocessor list, EU region, erasure across backups. Only then may OAuth exist, and only via a secret store outside git.

## Verification

`pytest` is the acceptance run. A manual CLI pass over `examples/class_a_annotations.py` checks the scan → approve → export path. There is no web UI in this increment, so browser verification does not apply.

## Risks

| Risk | What this plan does |
| --- | --- |
| A reviewer treats the draft as a finished technical file | Disclaimer is mandatory in every export. Export cannot happen silently. |
| The scanner copies a clinical fixture or a `.env` into SQLite | Denylist runs before parse. Tests use sentinels and assert the bytes are absent. |
| Class rules drift back to a 2006 blog summary | Class scaling lives in one function, `evidence_requirements`, covered by AC-06 through AC-08. |
| Free-tier seat count becomes a surveillance log of names | Seats are HMAC refs. Names of committers are not stored. |
