# Privacy Policy — DocuMDR

**Effective date:** 6 October 2026  
**Controller (once incorporated):** DocuMDR, Galway, Ireland  
**Supervisory authority:** Data Protection Commission, 6 Pembroke Row, Dublin 2, D02 X963, Ireland

This notice explains how DocuMDR processes personal data under the General Data Protection Regulation (EU) 2016/679, the Irish Data Protection Act 2018, and the European Communities (Electronic Communications Networks and Services) (Privacy and Electronic Communications) Regulations 2011 (S.I. 336/2011).

DocuMDR compiles draft technical documentation from software-development **metadata**. It is not a notified body, does not issue CE marking, does not provide legal or regulatory advice, and is not itself a medical device.

## 1. Roles

- **Controller** of account data: name, email address, organisation membership, role, and login security logs.
- **Processor** of customer git metadata: repository name, commit SHA, author handle (not email), redacted commit/PR text, relative file paths, and test summaries.
- The customer remains controller of any personal data that appears in their own repositories.

We do **not** ingest source code, patches, `.env` files, patient records, or special-category data (GDPR Art. 9). Connecting a repository that contains such data is contractually forbidden.

## 2. Lawful bases (Art. 6)

| Purpose | Basis |
|---------|--------|
| Creating an account and providing the service | Art. 6(1)(b) contract |
| Security, abuse prevention, session integrity | Art. 6(1)(f) legitimate interests (security of the service) |
| HITL signature audit trail | Art. 6(1)(c) legal obligation to keep quality records where applicable, otherwise Art. 6(1)(b) |
| Optional marketing email | Art. 6(1)(a) consent — **not collected in this version** |

## 3. What we collect

- Account: email (`example.com` addresses in the demo), display role (`engineer` or `quality`).
- Git events: handles, SHAs, paths, tags such as `#REQ-101`, redacted messages.
- Signatures: signer user id, role, timestamp, SHA scope, user agent.

We automatically redact emails, access tokens, private-key blocks, Irish PPS-like identifiers, NHS numbers, and IBANs before storage. Messages that still contain `PATIENT`, `MRN:`, or `DOB:` after redaction are **rejected**.

## 4. Retention

| Record | Period |
|--------|--------|
| Git events and compiled matrices | 24 months after organisation last activity |
| Authentication / security logs | 90 days |
| HITL signatures | 10 years, with personal identifiers minimised if the user is erased |
| Session cookies | Session / 7 days |

## 5. Your rights (Arts. 12–22)

You may request access, rectification, erasure, restriction, portability, and objection. Use **Account → Privacy** in the app (`/app/privacy`) to export JSON or erase your user record. You may also complain to the Data Protection Commission.

Erasure replaces author handles with `erased-{hash}` and signer display names with `user:{id}-erased`. Signature rows may be retained in minimised form for accountability.

## 6. Transfers and subprocessors

This version processes data in the EU/EEA only. There are no US subprocessors and no payment provider. Future Git hosting webhooks remain metadata-only; your git host is a separate service.

## 7. Cookies

Only a strictly necessary session cookie (`documdr_session`, HttpOnly, SameSite=Lax, Secure in production) is used. There are no analytics or advertising cookies.

## 8. Children

The service is B2B and intended for users aged 18 or over.

## 9. Contact

privacy@example.com (placeholder until incorporation). For demo deployments, use the in-app DSAR export.
