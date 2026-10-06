# DocuMDR MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a working DocuMDR compiler that ingests git metadata, builds IEC 62304 / ISO 14971 / EU MDR GSPR / EU AI Act Annex IV artefacts, blocks unsigned export, and honours GDPR erasure — with a self-serve demo UI and local CLI.

**Architecture:** TypeScript modular monolith. Pure domain libraries under `src/lib/*`, in-memory store for tests plus gitignored `data/documdr.json` for demo, Next.js App Router UI, CLI that reuses the parser/redactor and never opens a network socket.

**Tech Stack:** Node 22, TypeScript 5 strict, Next.js 15 App Router, React 19, Vitest 3, tsx CLI. No Stripe, no live OAuth, no PostgreSQL in this plan.

## Global Constraints

1. TypeScript strict, Node 22, Next.js App Router, Vitest.
2. No credentials or `.env` files in git except `.env.example` with empty values.
3. No patient/health special-category data; forbidden-content detector is mandatory on ingest.
4. Metadata only: never persist file bodies.
5. HITL required for export; DocuMDR never auto-signs.
6. Free tier: 3 contributors; export requires Team or higher.
7. Tag regex and GSPR ids as specified in `docs/superpowers/specs/2026-10-06-documdr-design.md` — exact.
8. Legal pages must exist and must not claim CE marking or notified-body status.
9. License remains MIT; add copyright notice in README.
10. Package name: `documdr`. UI product name: `DocuMDR`.
11. Demo emails use `example.com` only.
12. Persistence path `data/` is gitignored.

## File map (locked)

- Create: `.gitignore` — secrets, env, data, build, OS, IDE
- Create: `.dockerignore` — do not send `.env` or `data/` into images
- Create: `.env.example` — empty placeholders only
- Create: `package.json`, `tsconfig.json`, `vitest.config.ts`, `next.config.ts`
- Create: `src/lib/errors.ts`
- Create: `src/lib/privacy/redact.ts`
- Create: `src/lib/parser/tags.ts`
- Create: `src/lib/iec62304/traceability.ts`
- Create: `src/lib/iso14971/fmea.ts`
- Create: `src/lib/mdr/gspr.ts`
- Create: `src/lib/aiact/annex-iv.ts`
- Create: `src/lib/hitl/signature.ts`
- Create: `src/lib/billing/entitlements.ts`
- Create: `src/lib/store/types.ts`
- Create: `src/lib/store/memory.ts`
- Create: `src/lib/store/seed.ts`
- Create: `src/lib/ingest/events.ts`
- Create: `src/lib/compile/technical-file.ts`
- Create: `src/lib/gdpr/dsar.ts`
- Create: `src/lib/session.ts`
- Create: `src/cli/documdr.ts`
- Create: `src/app/**` Next.js routes
- Create: `tests/unit/*.test.ts`, `tests/integration/pipeline.test.ts`
- Create: `docs/legal/privacy-policy.md`, `terms.md`, `dpa.md`, `cookie-policy.md`, `dpia-note.md`
- Create: `README.md`
- Modify: none (greenfield besides `LICENSE`)

---

### Task 1: Repository foundation, ignore rules, and legal texts

**Files:**
- Create: `.gitignore`
- Create: `.dockerignore`
- Create: `.env.example`
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `vitest.config.ts`
- Create: `next.config.ts`
- Create: `src/lib/errors.ts`
- Create: `tests/unit/errors.test.ts`
- Create: `docs/legal/privacy-policy.md`
- Create: `docs/legal/terms.md`
- Create: `docs/legal/dpa.md`
- Create: `docs/legal/cookie-policy.md`
- Create: `docs/legal/dpia-note.md`
- Create: `README.md`

**Interfaces:**
- Consumes: MIT `LICENSE` already in repo
- Produces: `DocuMdrError`, `ForbiddenContentError`, `ExportBlockedError`, `UpgradeRequiredError`, `SeatLimitError`, `NotFoundError` from `src/lib/errors.ts`

- [ ] **Step 1: Write failing error-class test**

```ts
import { describe, expect, it } from "vitest";
import {
  DocuMdrError,
  ExportBlockedError,
  ForbiddenContentError,
} from "../../src/lib/errors";

describe("DocuMdrError", () => {
  it("ForbiddenContentError uses code FORBIDDEN_CONTENT", () => {
    const err = new ForbiddenContentError("patient data");
    expect(err).toBeInstanceOf(DocuMdrError);
    expect(err.code).toBe("FORBIDDEN_CONTENT");
    expect(err.message).toContain("patient data");
  });

  it("ExportBlockedError uses code EXPORT_BLOCKED", () => {
    expect(new ExportBlockedError("unsigned").code).toBe("EXPORT_BLOCKED");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/unit/errors.test.ts`
Expected: FAIL because `src/lib/errors.ts` does not exist (after package.json/vitest exist; create those first in this same task before the run).

Create `package.json`:

```json
{
  "name": "documdr",
  "version": "0.1.0",
  "private": true,
  "description": "DocuMDR — developer-first continuous regulatory integration for SaMD",
  "engines": { "node": ">=22" },
  "scripts": {
    "dev": "next dev --port 3000 --hostname 0.0.0.0",
    "build": "next build",
    "start": "next start --port 3000 --hostname 0.0.0.0",
    "test": "vitest run",
    "test:watch": "vitest",
    "cli": "tsx src/cli/documdr.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

`tsconfig.json` (strict, path `@/*` → `src/*`, includes `src` and `tests`).
`vitest.config.ts` uses `globals: false`, environment `node`, include `tests/**/*.test.ts`.
`next.config.ts` exports `{ reactStrictMode: true }`.

`.env.example`:

```
DEMO_MODE=true
SESSION_SECRET=
DATA_PATH=data/documdr.json
```

`.gitignore` must include at least: `node_modules/`, `.next/`, `out/`, `dist/`, `coverage/`, `.env`, `.env.*`, `!.env.example`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`, `data/`, `*.sqlite`, `credentials.json`, `serviceAccountKey.json`, `.vercel/`, OS junk, IDE junk, Python venvs, Docker override files. Un-ignore `.env.example`.

- [ ] **Step 3: Implement errors and legal docs**

```ts
export class DocuMdrError extends Error {
  readonly code: string;
  constructor(message: string, code: string) {
    super(message);
    this.name = new.target.name;
    this.code = code;
  }
}
export class ForbiddenContentError extends DocuMdrError {
  constructor(message: string) {
    super(message, "FORBIDDEN_CONTENT");
  }
}
export class ExportBlockedError extends DocuMdrError {
  constructor(message: string) {
    super(message, "EXPORT_BLOCKED");
  }
}
export class UpgradeRequiredError extends DocuMdrError {
  constructor(message: string) {
    super(message, "UPGRADE_REQUIRED");
  }
}
export class SeatLimitError extends DocuMdrError {
  constructor(message: string) {
    super(message, "SEAT_LIMIT");
  }
}
export class NotFoundError extends DocuMdrError {
  constructor(message: string) {
    super(message, "NOT_FOUND");
  }
}
```

Legal docs must state: Irish DPC contact; controller vs processor split; no CE marking; DocuMDR is not a notified body; no special-category/patient data; session cookies only; Art. 6 bases; 24-month metadata retention; 10-year minimised signatures; DSAR/erase; 18+ B2B.

README: product name DocuMDR, MIT, how to `npm test` and `npm run dev`, never commit `.env`.

- [ ] **Step 4: Run tests**

Run: `npm test`
Expected: PASS for errors.test.ts

- [ ] **Step 5: Commit**

```bash
git add .gitignore .dockerignore .env.example package.json tsconfig.json vitest.config.ts next.config.ts src/lib/errors.ts tests/unit/errors.test.ts docs/legal README.md package-lock.json
git commit -m "chore: DocuMDR foundation, gitignore, and legal texts"
```

---

### Task 2: Redactor and tag parser

**Files:**
- Create: `src/lib/privacy/redact.ts`
- Create: `src/lib/parser/tags.ts`
- Create: `tests/unit/redact.test.ts`
- Create: `tests/unit/tags.test.ts`

**Interfaces:**
- Consumes: `ForbiddenContentError`
- Produces:
  - `redactText(input: string): string`
  - `assertAllowedContent(input: string): void` — throws `ForbiddenContentError` if `PATIENT`, `MRN:`, or `DOB:` remain (case-insensitive) after redaction
  - `TAG_RE` and `parseTags(text: string): ParsedTag[]`
  - `type ParsedTag = { kind: TagKind; id: string; raw: string }`
  - `type TagKind = "REQ" | "RISK" | "TEST" | "ARCH" | "UNIT" | "GSPR" | "AI" | "SOUP" | "CAPA" | "MODEL"`
  - Regex exact: `/#(?<kind>REQ|RISK|TEST|ARCH|UNIT|GSPR|AI|SOUP|CAPA|MODEL)-(?<id>[A-Z0-9][A-Z0-9._-]{0,31})/g`

- [ ] **Step 1: Write failing redactor tests**

```ts
import { describe, expect, it } from "vitest";
import { ForbiddenContentError } from "../../src/lib/errors";
import { assertAllowedContent, redactText } from "../../src/lib/privacy/redact";

describe("redactText", () => {
  it("replaces emails", () => {
    expect(redactText("hi qa@example.com")).toBe("hi [REDACTED_EMAIL]");
  });
  it("replaces bearer tokens", () => {
    expect(redactText("Authorization: Bearer abcdefghijklmnop")).toContain("[REDACTED_SECRET]");
  });
  it("replaces AWS access keys", () => {
    expect(redactText("AKIAAAAAAAAAAAAAAAAA")).toContain("[REDACTED_SECRET]");
  });
  it("replaces Irish PPS-like tokens", () => {
    expect(redactText("PPS 1234567T")).toContain("[REDACTED_PPS]");
  });
  it("replaces NHS numbers", () => {
    expect(redactText("NHS 123 456 7890")).toContain("[REDACTED_NHS]");
  });
});

describe("assertAllowedContent", () => {
  it("throws on leftover clinical markers", () => {
    expect(() => assertAllowedContent("PATIENT John")).toThrow(ForbiddenContentError);
  });
  it("allows tagged engineering messages", () => {
    expect(() => assertAllowedContent("#REQ-101 add alarm")).not.toThrow();
  });
});
```

- [ ] **Step 2: Run to verify fail** then implement `redact.ts` (email RFC-like, `AKIA[0-9A-Z]{16}`, `Bearer\s+\S+`, `-----BEGIN [A-Z ]*PRIVATE KEY-----`, `\b\d{7}[A-Z]{1,2}\b`, `\b\d{3}\s?\d{3}\s?\d{4}\b`). Call redact inside `assertAllowedContent` first.

- [ ] **Step 3: Write failing parser tests**

```ts
it("parses mixed tags and ignores lowercase", () => {
  const tags = parseTags("see #REQ-101 and #RISK-04 and #req-nope");
  expect(tags.map((t) => t.raw)).toEqual(["#REQ-101", "#RISK-04"]);
});
it("parses GSPR dotted ids", () => {
  expect(parseTags("#GSPR-17.2")[0]).toEqual({
    kind: "GSPR",
    id: "17.2",
    raw: "#GSPR-17.2",
  });
});
```

- [ ] **Step 4: Implement parser; run `npx vitest run tests/unit/redact.test.ts tests/unit/tags.test.ts`; expect PASS**

- [ ] **Step 5: Commit** `feat: redact PII and parse regulatory tags`

---

### Task 3: IEC 62304 traceability matrix

**Files:**
- Create: `src/lib/iec62304/traceability.ts`
- Create: `tests/unit/traceability.test.ts`

**Interfaces:**
- Consumes: `ParsedTag`, `GitEvent` type from spec (define `src/lib/store/types.ts` here if not yet created — prefer creating `src/lib/types.ts` with `GitEvent` and `SoftwareItem` as in the spec)
- Produces:
  - `buildSoftwareItems(events: GitEvent[]): SoftwareItem[]`
  - `buildMatrix(items: SoftwareItem[], safetyClass: "A"|"B"|"C", events: GitEvent[]): MatrixRow[]`
  - `type MatrixRow = { reqId: string; archIds: string[]; unitIds: string[]; testIds: string[]; status: "covered"|"partial"|"gap" }`

Coverage rules (exact):
- Class A: REQ + ≥1 TEST with latest mentioning event `testSummary.failed === 0` → covered; else gap/partial
- Class B: also ≥1 ARCH
- Class C: also ≥1 UNIT
- `partial` if some required kinds present but not all, or tests failing
- Sort rows by `reqId` ascending
- Links: tags co-occurring on the same event are linked both ways

- [ ] **Step 1: Failing tests** for A covered, B missing ARCH = gap, C missing UNIT = partial if ARCH+TEST present, failing tests = partial, deterministic sort.

- [ ] **Step 2: Verify fail**

- [ ] **Step 3: Minimal implementation**

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit** `feat: IEC 62304 traceability matrix`

---

### Task 4: ISO 14971 FMEA

**Files:**
- Create: `src/lib/iso14971/fmea.ts`
- Create: `tests/unit/fmea.test.ts`

**Interfaces:**
- Produces:
  - `parseRiskFields(message: string): { severity?: 1|2|3|4|5; probability?: 1|2|3|4|5; detectability?: 1|2|3|4|5; hazard?: string; harm?: string; control?: string }`
  - `upsertRisks(rows: RiskRow[], event: GitEvent): RiskRow[]`
  - `verifyRiskControl(rows: RiskRow[], riskId: string): RiskRow[]`
  - `rpn(row): number` = S*P*D
  - `isUnacceptable(row): boolean` iff `rpn >= 40 && !controlsVerified`

Rules from spec: defaults 3/3/3; changePrompt on linked item/path change; probability +1 once per distinct sha cap 5; verify clears prompt and verified flag true, does not auto-lower P.

- [ ] **Steps:** TDD as Task 2. Commit `feat: ISO 14971 FMEA synchronization`

---

### Task 5: MDR GSPR and AI Act Annex IV

**Files:**
- Create: `src/lib/mdr/gspr.ts`
- Create: `src/lib/aiact/annex-iv.ts`
- Create: `tests/unit/gspr.test.ts`
- Create: `tests/unit/annex-iv.test.ts`

**Interfaces:**
- `GSPR_IDS` exact list from spec section 7
- `evaluateGspr(events: GitEvent[]): GsprRow[]` where `GsprRow = { id, title, status: "met"|"unmet" }`
- met only if `#GSPR-<id>` co-occurs with `#TEST-*` whose latest failed===0
- `compileAnnexIv(input: { providerName: string; events: GitEvent[]; risks: RiskRow[] }): AnnexIvFile`
- Nine sections numbered 1–9; section 8 `status: "not-signed"` always; section 9 includes manufacturer-not-DocuMDR incident sentence
- MODEL fields: `PURPOSE:`, `METRIC:`, `BIAS:`, `OVERSIGHT:`, `DATASET:` truncated 200 chars then redacted

- [ ] **Steps:** TDD. Commit `feat: MDR GSPR checklist and AI Act Annex IV compiler`

---

### Task 6: Store, ingest, entitlements, HITL

**Files:**
- Create: `src/lib/store/types.ts` (if not in Task 3)
- Create: `src/lib/store/memory.ts`
- Create: `src/lib/store/seed.ts`
- Create: `src/lib/ingest/events.ts`
- Create: `src/lib/billing/entitlements.ts`
- Create: `src/lib/hitl/signature.ts`
- Create: `tests/unit/entitlements.test.ts`
- Create: `tests/unit/ingest.test.ts`
- Create: `tests/unit/signature.test.ts`

**Interfaces:**
- `type Tier = "free" | "team" | "ai"`
- `type Role = "engineer" | "quality"`
- `MemoryStore` methods: `getOrg`, `listEvents`, `addEvent`, `getItems`/`setItems`, `getRisks`/`setRisks`, `addSignature`, `listSignatures`, `getUserByEmail`, `eraseUser`, `eraseOrganization`, `snapshot`
- `ingestGitEvent(store, event): void` — redact, assertAllowed, seat check, parse, upsert items/risks, persist redacted event (no file bodies)
- `contributorCount(orgId)` = max(invited users, distinct authorLogin last 30 days)
- Free seat limit 3, Team 25, AI 100
- `assertEntitlement(org, action)` per spec section 10
- `signTechnicalFile({org, user, shaScope, userAgent})` throws if role !== quality
- Meaning string exact from spec section 9

Seed: org `galway-demo`, tier `team`, class `B`, users `eng@example.com` engineer and `qa@example.com` quality, plus events covering REQ-101, ARCH-CORE, UNIT-ECG, TEST-UI, RISK-04, GSPR-17.2, MODEL-ECG-1.

- [ ] **Steps:** TDD including seat limit on 4th distinct author for free org; engineer cannot sign. Commit `feat: ingest pipeline, seats, and HITL signatures`

---

### Task 7: Technical file compiler and GDPR DSAR

**Files:**
- Create: `src/lib/compile/technical-file.ts`
- Create: `src/lib/gdpr/dsar.ts`
- Create: `tests/unit/compile.test.ts`
- Create: `tests/unit/dsar.test.ts`

**Interfaces:**
- `compileTechnicalFile(store, orgId): TechnicalFile` includes disclaimer exact from spec section 11, matrix, fmea, gspr, annexIv if entitled, signatures
- `exportTechnicalFile(store, orgId): TechnicalFile` throws `UpgradeRequiredError` on free; throws `ExportBlockedError` unless a quality signature exists with `shaScope === latest event sha`
- `createDsarExport(store, userId): object` JSON-serialisable account + authored events
- `eraseUser(store, userId): void` as spec
- Disclaimer constant:

```
DocuMDR compiles draft technical documentation from software-development metadata. It is not a notified body, does not issue CE marking, does not provide legal or regulatory advice, and is not itself a medical device. A qualified person must review and electronically sign artefacts before use. The manufacturer remains solely responsible for conformity with EU MDR 2017/745, IEC 62304, ISO 14971, ISO 13485, and Regulation (EU) 2024/1689.
```

- [ ] **Steps:** TDD unsigned export, signed export, DSAR, erase. Commit `feat: technical file export gates and GDPR DSAR`

---

### Task 8: Next.js PLG UI, CLI, and integration test

**Files:**
- Create: `src/app/layout.tsx`
- Create: `src/app/page.tsx`
- Create: `src/app/globals.css`
- Create: `src/app/privacy/page.tsx`
- Create: `src/app/terms/page.tsx`
- Create: `src/app/dpa/page.tsx`
- Create: `src/app/cookies/page.tsx`
- Create: `src/app/login/page.tsx`
- Create: `src/app/login/actions.ts`
- Create: `src/app/app/page.tsx`
- Create: `src/app/app/matrix/page.tsx`
- Create: `src/app/app/risks/page.tsx`
- Create: `src/app/app/gspr/page.tsx`
- Create: `src/app/app/ai-act/page.tsx`
- Create: `src/app/app/export/page.tsx`
- Create: `src/app/app/export/actions.ts`
- Create: `src/app/app/privacy/page.tsx`
- Create: `src/app/app/layout.tsx`
- Create: `src/lib/session.ts`
- Create: `src/lib/server-store.ts`
- Create: `src/cli/documdr.ts`
- Create: `tests/integration/pipeline.test.ts`
- Create: `tests/unit/cli.test.ts`

**Interfaces:**
- Demo login: POST email `qa@example.com` or `eng@example.com` (DEMO_MODE); session cookie `documdr_session` HttpOnly
- CLI: `tsx src/cli/documdr.ts parse --message <file>` writes JSON to stdout; exit 2 on ForbiddenContentError
- Integration test drives store only (no HTTP): seed → extra ingest → matrix → changePrompt → gspr met → unsigned export throws → sign → export has disclaimer → dsar → erase

UI copy must include product name **DocuMDR**, pricing €249 / €799, Galway/SaMD positioning, and the disclaimer. Engineer sees export blocked; quality can sign.

- [ ] **Step 1: Write integration + CLI failing tests**
- [ ] **Step 2: Verify fail**
- [ ] **Step 3: Implement CLI, session, pages, seed wiring**
- [ ] **Step 4: `npm test` all green; `npx tsc --noEmit` clean**
- [ ] **Step 5: Commit** `feat: DocuMDR demo UI, CLI, and end-to-end pipeline`

---

## Self-review vs spec

| Spec section | Task |
|--------------|------|
| Tag grammar | 2 |
| Redaction / forbidden content | 2, 6 |
| IEC 62304 | 3 |
| ISO 14971 | 4 |
| GSPR / Annex II | 5, 7 |
| AI Act Annex IV | 5 |
| HITL | 6, 7 |
| Entitlements | 6 |
| GDPR DSAR/erase/legal | 1, 7, 8 |
| CLI metadata-only | 8 |
| Gitignore / no secrets | 1 |
| PLG routes | 8 |

No TBD. Types named consistently: `GitEvent`, `SoftwareItem`, `MatrixRow`, `RiskRow`, `GsprRow`, `AnnexIvFile`, `TechnicalFile`.
