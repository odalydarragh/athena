import { randomUUID } from "node:crypto";
import { redactText, assertAllowedContent } from "../privacy/redact";
import { buildSoftwareItems } from "../iec62304/traceability";
import { upsertRisks } from "../iso14971/fmea";
import { assertSeatAvailable } from "../billing/entitlements";
import type { MemoryStore } from "../store/memory";
import type { GitEvent } from "../types";

export function ingestGitEvent(store: MemoryStore, event: GitEvent): void {
  store.getOrg(event.organizationId);
  const message = redactText(event.message);
  assertAllowedContent(message);
  const redacted: GitEvent = {
    ...event,
    message,
    paths: event.paths.slice(0, 200),
  };
  assertSeatAvailable(store, event.organizationId, redacted.authorLogin);
  store.addEvent(redacted);
  const org = store.getOrg(event.organizationId);
  store.setItems(
    org.id,
    buildSoftwareItems(store.listEvents(org.id), org.iec62304Class),
  );
  store.setRisks(org.id, upsertRisks(store.getRisks(org.id), redacted));
}

export function newEventId(): string {
  return randomUUID();
}
