import { parseTags } from "../parser/tags";
import type { GitEvent, MatrixRow, SafetyClass, SoftwareItem } from "../types";

const ITEM_KINDS = new Set(["REQ", "ARCH", "UNIT", "TEST", "SOUP"]);

function itemId(kind: string, id: string): string {
  return `${kind}-${id}`;
}

function firstLine(message: string): string {
  return message.split("\n")[0]?.trim() ?? message;
}

function latestEventForTest(events: GitEvent[], testId: string): GitEvent | undefined {
  const mentioning = events.filter((event) =>
    parseTags(event.message).some((tag) => itemId(tag.kind, tag.id) === testId),
  );
  if (mentioning.length === 0) return undefined;
  return [...mentioning].sort((a, b) => a.at.localeCompare(b.at) || a.sha.localeCompare(b.sha)).at(-1);
}

function testPassing(events: GitEvent[], testId: string): boolean {
  const latest = latestEventForTest(events, testId);
  return latest?.testSummary?.failed === 0;
}

export function buildSoftwareItems(
  events: GitEvent[],
  safetyClass: SafetyClass,
): SoftwareItem[] {
  const byId = new Map<string, SoftwareItem>();

  for (const event of events) {
    const tags = parseTags(event.message);
    const softwareTags = tags.filter((tag) => ITEM_KINDS.has(tag.kind));
    const allIds = tags.map((tag) => itemId(tag.kind, tag.id));

    for (const tag of softwareTags) {
      const id = itemId(tag.kind, tag.id);
      const linkedIds = allIds.filter((other) => other !== id);
      const existing = byId.get(id);
      if (existing) {
        existing.shas = [...new Set([...existing.shas, event.sha])];
        existing.linkedIds = [...new Set([...existing.linkedIds, ...linkedIds])];
        existing.paths = [...new Set([...existing.paths, ...event.paths])];
      } else {
        byId.set(id, {
          id,
          kind: tag.kind as SoftwareItem["kind"],
          title: firstLine(event.message),
          safetyClass,
          shas: [event.sha],
          linkedIds,
          paths: [...event.paths],
        });
      }
    }
  }

  return [...byId.values()].sort((a, b) => a.id.localeCompare(b.id));
}

function idsOfKind(item: SoftwareItem, kind: SoftwareItem["kind"], all: SoftwareItem[]): string[] {
  const fromLinks = item.linkedIds.filter((id) => all.find((other) => other.id === id)?.kind === kind);
  return [...new Set(fromLinks)].sort();
}

function coverageStatus(
  safetyClass: SafetyClass,
  archIds: string[],
  unitIds: string[],
  testIds: string[],
  testsPassing: boolean,
): MatrixRow["status"] {
  const hasArch = archIds.length > 0;
  const hasUnit = unitIds.length > 0;
  const hasTest = testIds.length > 0;

  if (safetyClass === "A") {
    if (testsPassing) return "covered";
    if (hasTest) return "partial";
    return "gap";
  }

  if (safetyClass === "B") {
    if (hasArch && testsPassing) return "covered";
    if (hasArch && hasTest) return "partial";
    return "gap";
  }

  if (hasArch && hasUnit && testsPassing) return "covered";
  if (hasArch && (hasUnit || hasTest)) return "partial";
  return "gap";
}

export function buildMatrix(
  items: SoftwareItem[],
  safetyClass: SafetyClass,
  events: GitEvent[],
): MatrixRow[] {
  const reqs = items.filter((item) => item.kind === "REQ");
  return reqs
    .map((req) => {
      const archIds = idsOfKind(req, "ARCH", items);
      const unitIds = idsOfKind(req, "UNIT", items);
      const testIds = idsOfKind(req, "TEST", items);
      const testsPassing =
        testIds.length > 0 && testIds.every((id) => testPassing(events, id));
      return {
        reqId: req.id,
        archIds,
        unitIds,
        testIds,
        status: coverageStatus(safetyClass, archIds, unitIds, testIds, testsPassing),
      };
    })
    .sort((a, b) => a.reqId.localeCompare(b.reqId));
}
