# DocuMDR

Developer-first **Continuous Regulatory Integration** for Software as a Medical Device (SaMD) teams. DocuMDR compiles draft IEC 62304 traceability matrices, ISO 14971 FMEA tables, EU MDR GSPR checklists, and EU AI Act Annex IV files from git **metadata** — not from Word documents.

Copyright (c) 2026 odalydarragh. Licensed under the MIT License; see `LICENSE`.

## What this is not

DocuMDR is **not** a notified body, does **not** issue CE marking, does **not** give legal advice, and is **not** itself a medical device. A qualified person must electronically sign artefacts before export. The manufacturer remains responsible for EU MDR 2017/745, IEC 62304, ISO 14971, ISO 13485, and Regulation (EU) 2024/1689.

## Quick start

```bash
cp .env.example .env.local   # leave SESSION_SECRET empty for demo mode
npm install
npm test
npm run dev
```

Open http://localhost:3000 and sign in with `qa@example.com` or `eng@example.com` (demo only).

Local metadata parser (no network):

```bash
npx tsx src/cli/documdr.ts parse --message path/to/commit.txt
```

## Privacy

- Never commit `.env`, keys, or `data/`.
- Ingest stores redacted metadata only.
- Legal texts: `docs/legal/`.

## Spec

- Design: `docs/superpowers/specs/2026-10-06-documdr-design.md`
- Plan: `docs/superpowers/plans/2026-10-06-documdr-mvp.md`
