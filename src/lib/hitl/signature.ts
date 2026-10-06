import { randomUUID } from "node:crypto";
import { SIGNATURE_MEANING, type Signature } from "../types";
import { NotFoundError } from "../errors";
import type { MemoryStore } from "../store/memory";

export function signTechnicalFile(
  store: MemoryStore,
  input: { orgId: string; userId: string; shaScope: string; userAgent: string },
): Signature {
  const user = store.getUser(input.userId);
  if (!user || user.organizationId !== input.orgId) {
    throw new NotFoundError("signer");
  }
  if (user.role !== "quality") {
    throw new Error("only a quality role may sign a technical file");
  }
  store.getOrg(input.orgId);
  const signature: Signature = {
    id: randomUUID(),
    organizationId: input.orgId,
    artefact: "technical-file",
    meaning: SIGNATURE_MEANING,
    signerUserId: user.id,
    signerRole: "quality",
    at: new Date().toISOString(),
    shaScope: input.shaScope,
    userAgent: input.userAgent,
  };
  store.addSignature(signature);
  return signature;
}
