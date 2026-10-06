import { compileAnnexIv } from "../aiact/annex-iv";
import { assertEntitlement } from "../billing/entitlements";
import { ExportBlockedError } from "../errors";
import { buildMatrix } from "../iec62304/traceability";
import { evaluateGspr } from "../mdr/gspr";
import type { MemoryStore } from "../store/memory";
import { DISCLAIMER, type TechnicalFile } from "../types";

export function compileTechnicalFile(store: MemoryStore, organizationId: string): TechnicalFile {
  const org = store.getOrg(organizationId);
  const events = store.listEvents(organizationId);
  const items = store.getItems(organizationId);
  const file: TechnicalFile = {
    disclaimer: DISCLAIMER,
    organizationId,
    headSha: store.latestSha(organizationId),
    matrix: buildMatrix(items, org.iec62304Class, events),
    fmea: store.getRisks(organizationId),
    gspr: evaluateGspr(events),
    signatures: store.listSignatures(organizationId),
  };
  if (org.tier === "ai" || org.modules.aiAct) {
    file.annexIv = compileAnnexIv({
      providerName: org.name,
      events,
      risks: file.fmea,
    });
  }
  return file;
}

export function exportTechnicalFile(store: MemoryStore, organizationId: string): TechnicalFile {
  const org = store.getOrg(organizationId);
  assertEntitlement(org, "export");
  const compiled = compileTechnicalFile(store, organizationId);
  const head = compiled.headSha;
  const signed = compiled.signatures.some(
    (signature) => signature.signerRole === "quality" && signature.shaScope === head,
  );
  if (!signed) {
    throw new ExportBlockedError("Human-in-the-loop quality signature required for this SHA");
  }
  return compiled;
}
