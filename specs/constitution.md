# DocuMDR constitution

DocuMDR is a local-first compiler that drafts software-lifecycle records from annotations a customer places in their own repository. These principles outrank convenience, roadmap pressure, and feature requests. A change that breaks one of them is out of spec even if the code is clever.

This document is a product constitution, not legal advice. Counsel still has to review the privacy notice, the processor terms, and any claim about regulatory sufficiency before the company is incorporated or a customer is charged.

## 1. Compiler, not signatory

DocuMDR drafts records. It does not declare conformity, apply a CE mark, act as a Notified Body, or sign an EU declaration of conformity. Every export states that in plain language.

A named person must record an approval gate (`approve_draft` or `reject`) before a draft file is written. The gate stores signer name, role, timestamp, and meaning. Version 1 does not claim an eIDAS qualified electronic signature. "Approve draft" means the named person accepts the draft for the customer's own review trail. It does not mean "I declare conformity."

## 2. Humans own risk judgment and classification

ISO 14971 probability, severity, residual-risk acceptance, and benefit-risk are human estimates. The engine must not invent them, default them, or treat a passing test as proof that a risk control is effective unless a person explicitly links that judgment.

EU MDR Annex VIII Rule 11 output is a record of what a person stated, plus a consistency note against the regulation's own sentences. It is always labelled a non-binding suggestion pending qualified review. The engine must not overwrite the person's stated class, and it must not ship a hidden decision tree that presents itself as MDCG 2019-11 applied automatically.

## 3. Local-first, no credentials in the product repository

The core engine runs on the customer's machine, reads files they point it at, and does not open network connections. Git history is read with local `git` only.

OAuth client secrets, personal access tokens, database URLs, and cloud credentials are out of scope until a later spec. They must not be committed, logged, or stored in the traceability database. `.env.example` stays empty.

## 4. Data protection by design

The customer is the controller for personal data in their repository when the CLI runs locally. DocuMDR does not become a processor of repository content in version 1, because that content is not uploaded.

- Store regulatory metadata (ids, short statements, paths, line numbers, content hashes). Do not store file bodies.
- Pseudonymise contributor emails with a per-tenant HMAC before anything is written. Do not store the raw email or the git author name.
- Do not put the HMAC salt in an access export.
- Special-category health data is out of purpose. Clinical containers (DICOM, HL7, EDF, NIfTI, FHIR patient payloads, and directories named for patient data) are skipped and their contents are not written to the store.
- Lines that look like secrets are redacted: path and line number only.
- Approver name and role are stored because the approval gate requires a named person. They are deleted with the tenant. Erasure does not delete the customer's git history and must not claim that it does.
- The local database and draft exports are owner-readable only.
- Version 1 has no analytics cookies, tracking pixels, or marketing SDK.
- Residency preference in version 1 is `eu_eea` only. Non-EEA processing is not a setting until a transfer spec exists.
- Enterprise Ireland funding does not change any of these duties.

## 5. Evidence scales with IEC 62304 class

Safety class follows IEC 62304:2006+AMD1:2015, not secondary summaries of the 2006 edition alone. Class A still requires system-test traceability. Class A does not require architecture, detailed design, unit verification, or integration records. Class B adds those except detailed design. Class C adds detailed design. The plan records this decision and the sources.

Gaps are shown in the draft. They do not replace the human gate, and a human may approve a draft that still lists gaps. The approval is bound to a fingerprint of the technical matrix. A later source change makes that approval stale.

## 6. Specs precede behavior

Behavior that matters to a customer, a reviewer, or a data subject is specified under `specs/` before the code changes. Tests cite the acceptance criteria. The core library stays free of network clients.

## 7. No presumption of conformity

The tool must not hardcode a claim that using it satisfies EN 62304, EN ISO 14971, EU MDR, or the EU AI Act. Harmonised status is a Commission decision and can change. FDA 510(k) assembly, EUDAMED filing, and Article 73 incident reporting are non-goals of the current spec.
