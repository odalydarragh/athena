import type { Organization, Tier } from "../types";
import { SeatLimitError, UpgradeRequiredError } from "../errors";
import type { MemoryStore } from "../store/memory";

export type EntitlementAction = "ingest" | "viewMatrix" | "viewFmea" | "viewGspr" | "viewAnnexIv" | "export";

const SEATS: Record<Tier, number> = {
  free: 3,
  team: 25,
  ai: 100,
};

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;

export function seatLimit(tier: Tier): number {
  return SEATS[tier];
}

export function contributorCount(store: MemoryStore, organizationId: string): number {
  const org = store.getOrg(organizationId);
  const cutoff = Date.now() - THIRTY_DAYS_MS;
  const authors = new Set(
    store
      .listEvents(organizationId)
      .filter((event) => Date.parse(event.at) >= cutoff)
      .map((event) => event.authorLogin),
  );
  const invited = Math.max(org.invitedUserIds.length, store.listUsers(organizationId).length);
  return Math.max(authors.size, invited);
}

export function assertEntitlement(org: Organization, action: EntitlementAction): void {
  if (action === "ingest" || action === "viewMatrix") return;
  if (action === "viewFmea" || action === "viewGspr" || action === "export") {
    if (org.tier === "free") throw new UpgradeRequiredError(`${action} requires Team or AI Governance`);
    return;
  }
  if (action === "viewAnnexIv") {
    if (org.tier !== "ai" && !org.modules.aiAct) {
      throw new UpgradeRequiredError("Annex IV requires AI Governance");
    }
  }
}

export function assertSeatAvailable(store: MemoryStore, organizationId: string, authorLogin: string): void {
  const org = store.getOrg(organizationId);
  const existing = new Set(
    store
      .listEvents(organizationId)
      .filter((event) => Date.parse(event.at) >= Date.now() - THIRTY_DAYS_MS)
      .map((event) => event.authorLogin),
  );
  const nextAuthors = new Set(existing).add(authorLogin);
  const next = Math.max(nextAuthors.size, org.invitedUserIds.length, store.listUsers(organizationId).length);
  if (next > seatLimit(org.tier)) {
    throw new SeatLimitError(`Free tier allows ${seatLimit(org.tier)} contributors`);
  }
}
