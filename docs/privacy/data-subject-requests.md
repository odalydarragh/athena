# Data-subject requests — local store

Version 1 can answer two requests for personal data the CLI itself has written. It cannot answer them for data that never left the customer's git host.

## Access

`python -m documdr access --tenant <id> --out access.json`

The JSON includes the tenant profile, projects, contributor refs, approval names and roles, and annotation metadata. It does not include the HMAC salt, raw commit emails, author names, or file bodies. The file is written mode `0600`.

Contributor refs are pseudonyms. Without the salt, which is not exported, the JSON is not a list of email addresses. Tell the requester that. If they want the emails, those are in the customer's git history, and the customer is the controller for that history.

## Erasure

`python -m documdr erase --tenant <id> --confirm <id>`

The confirm value must equal the tenant id. The command deletes that tenant's rows, including approval names, from the local database. It prints that git history was not modified.

Erasure of the local store does not delete GitHub, GitLab, backups the customer made, or clones on other machines. Article 17(3) can also require the customer to keep certain records for legal claims or regulatory traceability. The tool does not decide that. It only deletes its own copy.

## What the tool refuses to store in the first place

Credentials, private keys, token-bearing lines, DICOM, HL7, NIfTI, EDF, FHIR patient resources, and files under patient-data directories. A redaction entry may keep a path and a line number. It does not keep the line.
