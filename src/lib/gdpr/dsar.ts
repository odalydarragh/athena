import { createHash } from "node:crypto";
import { NotFoundError } from "../errors";
import type { MemoryStore } from "../store/memory";

function handleFor(email: string, displayName: string): string {
  return displayName || email.split("@")[0] || email;
}

function erasedLabel(userId: string): string {
  const hash = createHash("sha256").update(userId).digest("hex").slice(0, 12);
  return `erased-${hash}`;
}

export function createDsarExport(store: MemoryStore, userId: string): object {
  const user = store.getUser(userId);
  if (!user) throw new NotFoundError("user");
  const handle = handleFor(user.email, user.displayName);
  const events = store
    .listEvents(user.organizationId)
    .filter((event) => event.authorLogin === handle || event.authorLogin === user.email);
  return {
    user: {
      id: user.id,
      email: user.email,
      role: user.role,
      displayName: user.displayName,
      organizationId: user.organizationId,
    },
    events,
  };
}

export function eraseUser(store: MemoryStore, userId: string): void {
  const user = store.getUser(userId);
  if (!user) throw new NotFoundError("user");
  const handle = handleFor(user.email, user.displayName);
  const label = erasedLabel(userId);
  const events = store.listEvents(user.organizationId).map((event) =>
    event.authorLogin === handle || event.authorLogin === user.email
      ? { ...event, authorLogin: label }
      : event,
  );
  store.replaceEvents(user.organizationId, events);
  store.replaceSignatures(
    store.listAllSignatures().map((signature) =>
      signature.signerUserId === userId
        ? { ...signature, signerUserId: `user:${userId}-erased` }
        : signature,
    ),
  );
  store.deleteUser(userId);
}

export function eraseOrganization(store: MemoryStore, organizationId: string): void {
  store.eraseOrganization(organizationId);
}
