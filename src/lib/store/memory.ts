import { NotFoundError } from "../errors";
import type {
  GitEvent,
  Organization,
  RiskRow,
  Signature,
  SoftwareItem,
  User,
} from "../types";

export class MemoryStore {
  private orgs = new Map<string, Organization>();
  private users = new Map<string, User>();
  private events: GitEvent[] = [];
  private itemsByOrg = new Map<string, SoftwareItem[]>();
  private risksByOrg = new Map<string, RiskRow[]>();
  private signatures: Signature[] = [];

  putOrg(org: Organization): void {
    this.orgs.set(org.id, org);
  }

  putUser(user: User): void {
    this.users.set(user.id, user);
  }

  getOrg(id: string): Organization {
    const org = this.orgs.get(id);
    if (!org) throw new NotFoundError(`organisation ${id}`);
    return org;
  }

  getUser(id: string): User | undefined {
    return this.users.get(id);
  }

  getUserByEmail(email: string): User | undefined {
    return [...this.users.values()].find((user) => user.email === email);
  }

  listUsers(organizationId: string): User[] {
    return [...this.users.values()].filter((user) => user.organizationId === organizationId);
  }

  listEvents(organizationId: string): GitEvent[] {
    return this.events.filter((event) => event.organizationId === organizationId);
  }

  addEvent(event: GitEvent): void {
    this.events.push(event);
  }

  replaceEvents(organizationId: string, events: GitEvent[]): void {
    this.events = this.events.filter((event) => event.organizationId !== organizationId).concat(events);
  }

  getItems(organizationId: string): SoftwareItem[] {
    return this.itemsByOrg.get(organizationId) ?? [];
  }

  setItems(organizationId: string, items: SoftwareItem[]): void {
    this.itemsByOrg.set(organizationId, items);
  }

  getRisks(organizationId: string): RiskRow[] {
    return this.risksByOrg.get(organizationId) ?? [];
  }

  setRisks(organizationId: string, risks: RiskRow[]): void {
    this.risksByOrg.set(organizationId, risks);
  }

  addSignature(signature: Signature): void {
    this.signatures.push(signature);
  }

  replaceSignatures(next: Signature[]): void {
    this.signatures = next;
  }

  listSignatures(organizationId: string): Signature[] {
    return this.signatures.filter((signature) => signature.organizationId === organizationId);
  }

  listAllSignatures(): Signature[] {
    return [...this.signatures];
  }

  latestSha(organizationId: string): string | null {
    const events = [...this.listEvents(organizationId)].sort(
      (a, b) => a.at.localeCompare(b.at) || a.sha.localeCompare(b.sha),
    );
    return events.at(-1)?.sha ?? null;
  }

  deleteUser(userId: string): void {
    this.users.delete(userId);
  }

  eraseOrganization(organizationId: string): void {
    this.orgs.delete(organizationId);
    for (const user of this.listUsers(organizationId)) this.users.delete(user.id);
    this.events = this.events.filter((event) => event.organizationId !== organizationId);
    this.itemsByOrg.delete(organizationId);
    this.risksByOrg.delete(organizationId);
    this.signatures = this.signatures.filter((signature) => signature.organizationId !== organizationId);
  }

  snapshot(): {
    orgs: Organization[];
    users: User[];
    events: GitEvent[];
  } {
    return {
      orgs: [...this.orgs.values()],
      users: [...this.users.values()],
      events: [...this.events],
    };
  }
}
