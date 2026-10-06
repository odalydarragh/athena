# DocuMDR Design Specification

**Date:** 2026-10-06  
**Product:** DocuMDR (Continuous Regulatory Integration)  
**Venture:** Developer-first regulatory automation micro-SaaS for MedTech and SaMD, based in Galway, Ireland  
**Scope of this spec:** Months 1–6 core engine — a working, testable compiler that turns git metadata into IEC 62304, ISO 14971, EU MDR Annex II/III, and EU AI Act Annex IV artefacts, with Human-in-the-Loop (HITL) export gates and GDPR-by-design processing.  
**Out of scope:** Live GitHub/GitLab OAuth apps, paid Stripe billing, Notified Body legal sign-off, US FDA 510(k) module, Enterprise Ireland grant paperwork, and field sales.

This document is the implementation source of truth. The venture brief supplied the market thesis; this spec locks engineering behaviour.

---

## 1. Problem and success criteria

Early-stage Software as a Medical Device (SaMD) teams in Galway and the EU write software in git, but assemble Technical Files in Word/Excel. DocuMDR must:

1. Parse regulatory tags from commit messages, pull-request bodies, and inline comments.
2. Compile an IEC 62304 traceability matrix (requirements → architecture → units → tests).
3. Synchronise an ISO 14971 FMEA when a linked software item changes.
4. Populate an EU MDR Annex I General Safety and Performance Requirements (GSPR) checklist from verified tests.
5. Compile EU AI Act Annex IV sections from model-card metadata (no training-set files).
6. Block Technical File export until a designated quality reviewer applies an electronic signature.
7. Process **metadata only**. Do not ingest source code, patient data, or special-category data.
8. Enforce freemium seat limits (3 contributors on Free).
9. Provide data-subject access, export, and erasure.
10. Never store credentials in git. Ship a comprehensive `.gitignore` and `.env.example` with empty placeholders.

**Success for this delivery:** `npm test` is green; a demo organisation can ingest a sample webhook payload, view matrices, fail export without HITL, succeed after HITL, and complete a GDPR erasure.

**Non-goal:** DocuMDR is a **compiler and evidence binder**, not a Notified Body, not a manufacturer, and not itself a medical device. Generated files are drafts until a human signs them.

---

## 2. Approaches considered

### Approach A — TypeScript modular monolith (recommended)

One Next.js App Router application plus pure TypeScript domain libraries (`src/lib/*`) and a local CLI that reuses those libraries.

- **Pros:** Ten-minute self-serve path; one language; domain engines unit-testable without HTTP; CLI can run offline so proprietary source never leaves the customer machine.
- **Cons:** Parser is not independently scaled; SQLite/JSON persistence is not multi-region.

### Approach B — Python FastAPI engine + separate React SPA

- **Pros:** Strong scientific parsing libraries.
- **Cons:** Two runtimes, CORS, duplicated types, slower Product-Led Growth (PLG) loop. Rejected for Months 1–6.

### Approach C — Event-sourced microservices

Ingest, compile, export, and billing as separate services.

- **Pros:** Scale and isolation.
- **Cons:** Infra before first beta user. Rejected until HPSU-scale traffic exists.

**Decision:** Approach A. Persistence is an in-memory store for tests and a gitignored JSON file (`data/documdr.json`) for local demo. The store interface is persistence-agnostic so PostgreSQL can replace it later without changing domain code.

---

## 3. Architecture

```
Git host / CI                  DocuMDR (this repo)
┌─────────────────┐            ┌──────────────────────────────────────┐
│ commits, PRs,   │  metadata  │  ingest (webhook or CLI)             │
│ test summaries  │ ─────────► │  redact PII / secrets                │
│ tagged #REQ-…   │  only      │  parse tags                          │
└─────────────────┘            │  IEC 62304 matrix                    │
                               │  ISO 14971 FMEA                      │
Local CLI (Docker/node)        │  MDR GSPR checklist                  │
parses in customer CI;         │  AI Act Annex IV                     │
uploads metadata, not trees    │  entitlements (seats / modules)      │
                               │  HITL signature gate                 │
                               │  technical file compiler             │
                               │  GDPR DSAR / erase                   │
                               └──────────────────────────────────────┘
```

**Units (one purpose each):**

| Unit | Path | Does | Depends on |
|------|------|------|------------|
| Tag parser | `src/lib/parser/tags.ts` | Extract typed tags from text | none |
| Redactor | `src/lib/privacy/redact.ts` | Strip emails, secrets, NHS/IE PPS patterns | none |
| Traceability | `src/lib/iec62304/traceability.ts` | Build software items and matrix | parser types |
| FMEA | `src/lib/iso14971/fmea.ts` | Risk rows, RPN, change prompts | parser types |
| GSPR | `src/lib/mdr/gspr.ts` | Annex I software-relevant checklist | tests + tags |
| Annex IV | `src/lib/aiact/annex-iv.ts` | Nine-section AI Act file | model metadata |
| HITL | `src/lib/hitl/signature.ts` | Electronic signature records | org users |
| Entitlements | `src/lib/billing/entitlements.ts` | Free/Team/AI Governance gates | org |
| Compiler | `src/lib/compile/technical-file.ts` | Assemble export; require HITL | all engines |
| Store | `src/lib/store/memory.ts` | Org, users, events, artefacts | none |
| GDPR | `src/lib/gdpr/dsar.ts` | Export and erase personal data | store |
| Ingest | `src/lib/ingest/events.ts` | Apply a redacted git event | parser, fmea |
| Web | `src/app/*` | PLG dashboard | store + engines |
| CLI | `src/cli/documdr.ts` | Local parse → metadata JSON | parser, redact |

DocuMDR **does not** sign CE declarations. Export packages include a fixed disclaimer and require `role === "quality"`.

---

## 4. Tag grammar

Tags are case-sensitive, ASCII, and must match:

```
#(?<kind>REQ|RISK|TEST|ARCH|UNIT|GSPR|AI|SOUP|CAPA|MODEL)-(?<id>[A-Z0-9][A-Z0-9._-]{0,31})
```

Examples: `#REQ-101`, `#RISK-04`, `#TEST-UNIT-12`, `#GSPR-17.2`, `#MODEL-ECG-1`.

A git event supplies:

```ts
type GitEvent = {
  id: string;
  organizationId: string;
  repository: string;      // "org/repo" — no clone URL secrets
  sha: string;             // 7–40 hex
  at: string;              // ISO-8601
  authorLogin: string;     // handle only, not email
  message: string;         // redacted before persist
  paths: string[];         // relative paths, max 200, no file bodies
  testSummary?: { passed: number; failed: number; skipped: number };
};
```

**Forbidden in persistable events:** file contents, patches, `.env` values, patient identifiers, full emails (redact to `[REDACTED_EMAIL]`).

---

## 5. IEC 62304 engine

Safety class is selected per project: `A | B | C` (IEC 62304:2006+AMD1:2015).

The engine maintains software items:

```ts
type SoftwareItem = {
  id: string;              // tag id, e.g. "REQ-101"
  kind: "REQ" | "ARCH" | "UNIT" | "TEST" | "SOUP";
  title: string;           // first line of the originating message
  safetyClass: "A" | "B" | "C";
  shas: string[];
  linkedIds: string[];     // other tags co-occurring on the same event
};
```

**Traceability matrix rows:** each `REQ` must list linked `ARCH`, `UNIT`, and `TEST` ids. Coverage status:

- `covered` — REQ has ≥1 ARCH (if class B or C), ≥1 UNIT (if class C), and ≥1 TEST with `testSummary.failed === 0` on the latest event that mentions the TEST.
- `partial` — some but not all required links.
- `gap` — missing a required link for the project safety class.

Class A does not require ARCH or UNIT links. Class B requires ARCH. Class C requires ARCH and UNIT.

The matrix must be deterministic: sort items by `id` ascending.

---

## 6. ISO 14971 FMEA engine

```ts
type RiskRow = {
  id: string;              // "RISK-04"
  hazard: string;
  sequence: string;
  harm: string;
  severity: 1 | 2 | 3 | 4 | 5;
  probability: 1 | 2 | 3 | 4 | 5;
  detectability: 1 | 2 | 3 | 4 | 5;
  rpn: number;             // S * P * D
  linkedItemIds: string[];
  controls: string[];
  controlsVerified: boolean;
  changePrompt: boolean;   // true after linked path/tag change until re-verify
};
```

Rules:

- Creating a `#RISK-*` tag without severity defaults to `severity=3`, `probability=3`, `detectability=3` (RPN 27) and `controlsVerified=false`.
- Optional structured fields in the message: `S:4 P:2 D:3 HAZARD:... HARM:... CONTROL:...`.
- When a later git event mentions both a risk id and a linked software item (or a path already associated with that item), set `changePrompt=true` and `controlsVerified=false`. Increment `probability` by 1 (cap 5) **once per distinct sha**.
- `rpn >= 40` is `unacceptable` until controls are verified.
- `verifyRiskControl(riskId, reviewerId)` sets `controlsVerified=true`, `changePrompt=false`, and does not auto-lower probability (human records residual probability via a new event message `P:n`).

---

## 7. EU MDR Annex II / GSPR builder

DocuMDR populates a **software-relevant** GSPR checklist (MDR Annex I), not the entire hardware catalogue. Canonical ids:

| GSPR id | Title |
|---------|--------|
| 1 | General safety |
| 2 | Risk reduction |
| 3 | Risk management system |
| 4 | Risk control / residual risk |
| 5 | Use error |
| 14.2 | IT security / unauthorised access |
| 17.1 | Repeatability, reliability, performance of software |
| 17.2 | State of the art software lifecycle (IEC 62304) |
| 17.3 | IT security for programmable systems |
| 17.4 | Mobile / connected platforms |
| 22 | Interoperability with other devices |
| 23.1 | Information supplied by the manufacturer |

A GSPR item is `met` only when at least one `#GSPR-<id>` tag co-occurs with a `#TEST-*` whose latest `testSummary.failed === 0`. Otherwise `unmet`. Annex II technical-file sections compiled:

1. Device description (project name, class IIa default, intended purpose string).
2. GSPR checklist.
3. Risk management file pointer (FMEA table).
4. Software verification evidence (test summaries by sha).
5. Label / IFU placeholder from `#GSPR-23.1`.

Default project profile: `mdrClass: "IIa"`, `rule: "11"`, `iec62304Class` as configured.

---

## 8. EU AI Act Annex IV module

When the project enables `modules.aiAct` (AI Governance tier), compile nine sections matching Regulation (EU) 2024/1689 Annex IV:

1. General description (`#MODEL-*` intended purpose, provider name, version = latest sha).
2. Elements and development process (methods from model-card fields).
3. Monitoring, functioning, control (accuracy, limitations, human oversight).
4. Appropriateness of performance metrics.
5. Risk management (reuse ISO 14971 rows tagged `#AI-*` or linked to a MODEL).
6. Lifecycle changes (git events mentioning MODEL ids).
7. Harmonised standards list (static: IEC 62304, ISO 14971, ISO 13485 — user-editable later).
8. EU declaration of conformity — **always** `status: "not-signed"`; DocuMDR never generates a signed DoC.
9. Post-market monitoring plan placeholder.

Model-card fields parsed from messages:

```
#MODEL-ECG-1 PURPOSE:... METRIC:auroc=0.91 BIAS:... OVERSIGHT:... DATASET:deidentified-summary-only
```

**Refuse** to store dataset payloads. If a message contains `DATASET:` the value is truncated to 200 characters and must not include emails or numeric patient ids (redactor).

Article 73 incident reporting is **out of scope** except a stub section titled “Incident reporting is performed by the manufacturer, not DocuMDR.”

---

## 9. HITL electronic signatures

ISO 13485 / EU AI Act governance: quality managers retain authority.

```ts
type Signature = {
  id: string;
  organizationId: string;
  artefact: "technical-file";
  meaning: "I have reviewed this compiled technical file. I am authorised to approve it for internal use. DocuMDR is not a Notified Body.";
  signerUserId: string;
  signerRole: "quality";
  at: string;
  shaScope: string;        // HEAD sha compiled
  userAgent: string;
};
```

Rules:

- Only `role: "quality"` may sign.
- `role: "engineer"` may ingest and view, never export.
- Export without a signature whose `shaScope` equals the compiled HEAD sha throws `ExportBlockedError`.
- Signatures are append-only audit records. Erasure of a user replaces signer display name with `user:{id}-erased` but keeps the signature row (accountability vs storage limitation: retain 10 years as regulatory record, with personal identifiers minimised).

This is a **simple electronic signature** (eIDAS), not a qualified certificate. UI must label it as such.

---

## 10. Billing and entitlements

| Tier | Price | Contributors | Modules |
|------|-------|--------------|---------|
| Free | €0 | 3 | IEC 62304 matrix only |
| Team | €249 / month | 25 | + ISO 14971 + MDR GSPR |
| AI Governance | €799 / month | 100 | + Annex IV + export package |

`assertEntitlement(org, action)`:

- `ingest` — allowed all tiers if `contributorCount <= seatLimit`.
- `viewMatrix` — all tiers.
- `viewFmea` / `viewGspr` — Team or AI Governance.
- `viewAnnexIv` / `export` — AI Governance only for Annex IV; Team+ for MDR export; Free may **preview** matrix but `export` throws `UpgradeRequiredError`.

Contributor count = distinct `authorLogin` values on events in the last 30 days, plus invited users, whichever is higher.

No payment processor in this MVP. Tier is an organisation field defaulting to `free`. Demo org is `team`.

---

## 11. GDPR, ePrivacy, and Irish law

**Supervisory authority:** Data Protection Commission, 6 Pembroke Row, Dublin 2, D02 X963, Ireland.

**Roles:**

- DocuMDR Ltd (once incorporated) is **controller** of account data: name, email, hashed password or magic-link token, org membership, IP on login.
- DocuMDR is **processor** of customer git metadata (handles, SHAs, redacted messages, paths).
- The customer remains controller of any personal data that appears in their repositories. We contractually forbid uploading special-category or patient data.

**Lawful bases (Art. 6 GDPR):**

| Processing | Basis |
|------------|--------|
| Account, auth, providing the service | Art. 6(1)(b) contract |
| Security logs, abuse | Art. 6(1)(f) legitimate interests (security) |
| Optional product email | Art. 6(1)(a) consent — **not collected in MVP** |
| Signature audit retention | Art. 6(1)(c) legal obligation / Art. 9 not applicable (no health data of patients) |

**Data minimisation (implemented in code, not policy only):**

1. Ingest paths and tags, never blobs.
2. Redact before persist: emails, Bearer/JWT-like tokens, AWS keys, private key armor, Irish PPS (`\d{7}[A-Z]{1,2}`), UK NHS (`\d{3}\s?\d{3}\s?\d{4}`), IBAN.
3. Store `authorLogin`, never author email from git.
4. Reject events whose message still matches `PATIENT`, `MRN:`, or `DOB:` after redaction (`ForbiddenContentError`).
5. Session cookie is `HttpOnly`, `SameSite=Lax`, `Secure` in production; strictly necessary; no analytics cookies in MVP (ePrivacy S.I. 336/2011).

**Retention:**

| Record | Period |
|--------|--------|
| Git events / matrices | 24 months after org last activity, then delete |
| Auth logs | 90 days |
| HITL signatures | 10 years, identifiers minimised on user erasure |
| Support tickets | none in MVP |

**Data subject rights (Art. 12–22):** `createDsarExport(userId)` returns JSON of that user’s account and events they authored. `eraseUser(userId)` deletes account fields, redacts `authorLogin` on events to `erased-{hash}`, and anonymises signatures as above. `eraseOrganization(orgId)` deletes all processor data for that tenant except minimised signature hashes if legally required — for MVP, demo erasure deletes everything including signatures **when the org is Free and has zero signed exports**; otherwise signatures remain minimised. Provide a `/privacy` page describing this.

**Security (Art. 32):** no secrets in repo; passwords (if any) hashed with scrypt; demo uses a well-known test login **documented as test-only** (`qa@example.com` / not a production password — demo mode skips password and uses a session seeded in development). TLS assumed at the platform. JSON store file mode `0600`.

**International transfers:** default processing in the EU/EEA. No US subprocessors in MVP. If GitHub webhooks are later enabled, webhook payloads are still metadata-only; GitHub remains a separate controller/processor of the customer’s git hosting.

**DPIA:** a lightweight DPIA note lives in `docs/legal/dpia-note.md`. Residual risk is not high because we refuse health data and source code. If that policy changes, consult the DPC before processing.

**Children:** B2B service, 18+ only.

**Medical/regulatory disclaimers** on every export and the landing page:

> DocuMDR compiles draft technical documentation from software-development metadata. It is not a notified body, does not issue CE marking, does not provide legal or regulatory advice, and is not itself a medical device. A qualified person must review and electronically sign artefacts before use. The manufacturer remains solely responsible for conformity with EU MDR 2017/745, IEC 62304, ISO 14971, ISO 13485, and Regulation (EU) 2024/1689.

Legal pages are **not** legal advice; they are operational implementations of the principles above.

---

## 12. Security of the repository itself

- Comprehensive `.gitignore` composed from GitHub’s Node, Next.js, Python, Docker, OS, and secrets templates, plus DocuMDR data dirs.
- `.env.example` lists `DEMO_MODE=true` and empty `SESSION_SECRET=` — never real values.
- `.dockerignore` must not copy `.env` or `data/`.
- No API keys, PEM files, or `credentials.json` in the tree.
- Pre-commit mindset: tests must fail if redactor lets an email persist.

---

## 13. Web application (PLG)

Routes:

| Path | Auth | Purpose |
|------|------|---------|
| `/` | public | Positioning, pricing, disclaimers, Galway/SaMD story |
| `/privacy` `/terms` `/dpa` `/cookies` | public | Legal |
| `/login` | public | Demo login |
| `/app` | session | Org home: connected repo (simulated), safety class selector |
| `/app/matrix` | session | IEC 62304 matrix |
| `/app/risks` | session + Team | FMEA |
| `/app/gspr` | session + Team | GSPR checklist |
| `/app/ai-act` | session + AI | Annex IV |
| `/app/export` | session + Team | HITL sign + download |
| `/app/privacy` | session | DSAR export / erase self |

Demo seed (`src/lib/store/seed.ts`) creates:

- Org `galway-demo`, tier `team`, class `B`, MDR IIa Rule 11.
- Users: `eng@example.com` (engineer), `qa@example.com` (quality).
- Events covering REQ-101, ARCH-CORE, UNIT-ECG, TEST-UI, RISK-04, GSPR-17.2, MODEL-ECG-1.

UI: high-contrast, developer-dense, not a consumer marketing toy. Desktop-first; usable at 1280px. No dark-pattern consent walls.

---

## 14. CLI

`npx tsx src/cli/documdr.ts parse --message FILE --out metadata.json`

Reads a commit message (and optional `--paths` list). Writes redacted metadata JSON. Exit `2` on `ForbiddenContentError`. Does not network.

---

## 15. Error model

```ts
class DocuMdrError extends Error { code: string }
class ForbiddenContentError extends DocuMdrError // 422
class ExportBlockedError extends DocuMdrError    // 403
class UpgradeRequiredError extends DocuMdrError  // 402
class SeatLimitError extends DocuMdrError        // 403
class NotFoundError extends DocuMdrError         // 404
```

---

## 16. Testing

- Framework: Vitest.
- TDD for every domain unit. Tests live in `tests/unit/*.test.ts` and `tests/integration/*.test.ts`.
- No production network. No real OAuth.
- Integration test: seed → ingest event → matrix coverage → risk changePrompt → GSPR met → unsigned export throws → quality signs → export JSON contains disclaimer and GSPR table → DSAR → erase.

---

## 17. Global constraints (binding)

1. TypeScript strict, Node 22, Next.js App Router, Vitest.
2. No credentials or `.env` files in git except `.env.example` with empty values.
3. No patient/health special-category data; forbidden-content detector is mandatory on ingest.
4. Metadata only: never persist file bodies.
5. HITL required for export; DocuMDR never auto-signs.
6. Free tier: 3 contributors; export requires Team or higher.
7. Tag regex and GSPR ids as specified in this document — exact.
8. Legal pages must exist and must not claim CE marking or notified-body status.
9. License remains MIT; add copyright notice in README.
10. Package name: `documdr`. UI product name: `DocuMDR`.
11. Demo emails use `example.com` only.
12. Persistence path `data/` is gitignored.

---

## 18. File map

```
.gitignore
.dockerignore
.env.example
LICENSE
README.md
package.json
tsconfig.json
vitest.config.ts
next.config.ts
src/app/...
src/cli/documdr.ts
src/lib/**/*.ts
tests/**/*.test.ts
docs/legal/*.md
docs/superpowers/specs/2026-10-06-documdr-design.md
docs/superpowers/plans/2026-10-06-documdr-mvp.md
```

---

## 19. Spec self-review

- Placeholders: none. Tier prices, seat limits, GSPR ids, tag regex, retention periods, and routes are explicit.
- Consistency: compiler requires HITL; Free cannot export; AI Act DoC is never signed; ingest redacts then forbids leftover clinical identifiers.
- Scope: Months 1–6 engine + PLG demo UI. Live OAuth and Stripe deferred.
- Ambiguity resolved: contributor counting uses 30-day distinct `authorLogin` vs invited users, higher wins; probability increments once per sha; class A/B/C link rules stated.
