# DocuMDR

DocuMDR drafts IEC 62304 traceability records from annotations in a repository on your machine. The draft is not a conformity assessment, not legal or regulatory advice, and not a Notified Body opinion. Read `docs/disclaimer.md` before you use an export for anything else.

Version 1 is the local compiler from `specs/001-local-traceability-engine/spec.md`. It does not call GitHub, GitLab, or any other network service, and it does not ship with credentials. Hosted OAuth waits on a later spec, a data-processing agreement, and an EU hosting decision.

## Spec-driven layout

`specs/constitution.md` is the product constitution. Feature behavior is `specs/001-local-traceability-engine/`. Code in `src/documdr/` implements that spec. Tests cite its acceptance criteria.

## Run

```bash
pip install -e ".[dev]"
pytest
python -m documdr scan examples --tenant demo --project class-a --class A
python -m documdr approve --tenant demo --project class-a --name "A. Quinn" --role "RA/QA" --meaning approve_draft
python -m documdr export --tenant demo --project class-a --out /tmp/class-a-draft.md
```

The database defaults to `./.documdr/store.sqlite`. That directory is gitignored. File mode is owner read/write.

Tag grammar and the class rules are in the spec. A short synthetic example is `examples/class_a_annotations.py`.

## Privacy

The scanner stores tag metadata, paths, line numbers, content hashes, and an HMAC of a contributor email when git has one. It does not store the email, the author name, or file bodies. Clinical files, secret lines, and private keys are skipped. `access` writes a copy of what the local store holds. `erase --confirm <tenant>` deletes those rows and does not delete git history.

See `docs/privacy/processing-record.md` and `docs/privacy/data-subject-requests.md`. Those notes are drafts for counsel, not a finished Article 30 record. The company is not incorporated yet.

## What does not belong in git

Secrets, OAuth tokens, the local database, draft exports, and patient or clinical data. `.gitignore` is the enforcement list. `.env.example` is committable only while every value stays empty.
