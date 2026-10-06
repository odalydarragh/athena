# Draft record of processing — local CLI

This is a working record for the version 1 command-line tool. It is not a finished Article 30 record, not a privacy notice, and not legal advice. Complete the controller identity after incorporation and have counsel review it before any customer data is processed on DocuMDR infrastructure. Enterprise Ireland or LEO funding does not change these duties.

## Controller identity

Not yet incorporated. The venture plan intends a company established in Galway, Ireland. Until that exists, the person running the CLI on their own machine is the one deciding why repository data is parsed. Do not invent a company number or a DPO appointment here.

If the company is later established in Ireland and offers a cross-border service, the Data Protection Commission is the likely lead supervisory authority under GDPR Article 56. That has to be confirmed from the actual place of central administration, not from this note.

## This version

| Question | Answer for the local CLI |
| --- | --- |
| Who decides purposes and means of parsing a repository? | The customer, on their own machine. They are the controller for contributor data in their git history. |
| Does DocuMDR receive repository contents? | No. The process does not open a network connection. |
| Is DocuMDR a processor of those contents? | No, not in this version. A hosted product would be a processor and would need Article 28 terms before it is switched on. See constitution principle 4. |
| What does the local database hold? | Tag metadata, file paths, line numbers, content hashes, commit shas, HMAC contributor refs, and approval names and roles. See `specs/001-local-traceability-engine/data-model.md`. |
| Special-category data | Out of purpose. Health data, DICOM, HL7, and FHIR patient payloads are skipped and not written to the store (GDPR Article 9, Article 4(15)). |
| Lawful basis | Not asserted on behalf of customers. A customer processing employee git identities typically relies on contract or legitimate interests and must document that themselves. Approval names are stored because the customer asked the tool to keep a named review gate. |
| Retention | Until the operator runs `erase` for that tenant, or deletes the database file. There is no silent copy. |
| Recipients and subprocessors | None in version 1. No analytics cookies and no tracking pixels. |
| Transfers outside the EEA | None by the tool. The residency field accepts only `eu_eea`. |
| Security (Article 32) | Owner-only file permissions on the database and exports, tenant-scoped queries, secret redaction, no secrets in logs, HMAC in place of emails. |

## Sources consulted while writing the product rules

- Regulation (EU) 2016/679, Articles 4, 5, 9, 15, 17, 25, 28, 30, 32, and 56. EUR-Lex CELEX:32016R0679.
- EDPB Guidelines 4/2019 on Article 25 (data protection by design and by default).
- Directive 2002/58/EC Article 5(3) on storing information on terminal equipment, as a reason version 1 has no non-essential cookies.

Counsel should replace this section with the company's own notice before publication.
