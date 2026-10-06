import { ingestGitEvent } from "../ingest/events";
import type { MemoryStore } from "./memory";

export function seedDemo(store: MemoryStore): void {
  store.putOrg({
    id: "galway-demo",
    name: "Galway Demo Ltd",
    tier: "team",
    iec62304Class: "B",
    mdrClass: "IIa",
    rule: "11",
    modules: { aiAct: false },
    invitedUserIds: ["user-eng", "user-qa"],
  });
  store.putUser({
    id: "user-eng",
    organizationId: "galway-demo",
    email: "eng@example.com",
    role: "engineer",
    displayName: "eng",
  });
  store.putUser({
    id: "user-qa",
    organizationId: "galway-demo",
    email: "qa@example.com",
    role: "quality",
    displayName: "qa",
  });

  ingestGitEvent(store, {
    id: "evt-1",
    organizationId: "galway-demo",
    repository: "galway/samd-demo",
    sha: "aa10101",
    at: "2026-10-01T09:00:00.000Z",
    authorLogin: "eng",
    paths: ["src/alarm.ts"],
    message: "#REQ-101 #ARCH-CORE #UNIT-ECG #TEST-UI #GSPR-17.2 IEC 62304 alarm limit",
    testSummary: { passed: 8, failed: 0, skipped: 0 },
  });
  ingestGitEvent(store, {
    id: "evt-2",
    organizationId: "galway-demo",
    repository: "galway/samd-demo",
    sha: "bb20202",
    at: "2026-10-01T10:00:00.000Z",
    authorLogin: "eng",
    paths: ["src/alarm.ts"],
    message: "#RISK-04 #REQ-101 S:3 P:2 D:2 HAZARD:missed-alarm HARM:delayed-therapy CONTROL:redundant-alert",
  });
  ingestGitEvent(store, {
    id: "evt-3",
    organizationId: "galway-demo",
    repository: "galway/samd-demo",
    sha: "cc30303",
    at: "2026-10-01T11:00:00.000Z",
    authorLogin: "eng",
    paths: ["models/ecg.py"],
    message:
      "#MODEL-ECG-1 PURPOSE:rhythm-triage METRIC:auroc=0.91 BIAS:age-band OVERSIGHT:cardiologist DATASET:deidentified-summary-only",
  });
}
