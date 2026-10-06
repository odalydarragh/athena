import { parseTags } from "../parser/tags";
import type { GitEvent, GsprRow } from "../types";

export const GSPR_IDS: Array<{ id: string; title: string }> = [
  { id: "1", title: "General safety" },
  { id: "2", title: "Risk reduction" },
  { id: "3", title: "Risk management system" },
  { id: "4", title: "Risk control / residual risk" },
  { id: "5", title: "Use error" },
  { id: "14.2", title: "IT security / unauthorised access" },
  { id: "17.1", title: "Repeatability, reliability, performance of software" },
  { id: "17.2", title: "State of the art software lifecycle (IEC 62304)" },
  { id: "17.3", title: "IT security for programmable systems" },
  { id: "17.4", title: "Mobile / connected platforms" },
  { id: "22", title: "Interoperability with other devices" },
  { id: "23.1", title: "Information supplied by the manufacturer" },
];

function testPassing(events: GitEvent[], testFullId: string): boolean {
  const mentioning = events.filter((event) =>
    parseTags(event.message).some((tag) => tag.kind === "TEST" && `TEST-${tag.id}` === testFullId),
  );
  const latest = [...mentioning].sort((a, b) => a.at.localeCompare(b.at) || a.sha.localeCompare(b.sha)).at(-1);
  return latest?.testSummary?.failed === 0;
}

export function evaluateGspr(events: GitEvent[]): GsprRow[] {
  const testsByGspr = new Map<string, Set<string>>();

  for (const event of events) {
    const tags = parseTags(event.message);
    const gsprs = tags.filter((tag) => tag.kind === "GSPR");
    const tests = tags.filter((tag) => tag.kind === "TEST").map((tag) => `TEST-${tag.id}`);
    for (const gspr of gsprs) {
      const set = testsByGspr.get(gspr.id) ?? new Set<string>();
      for (const testId of tests) set.add(testId);
      testsByGspr.set(gspr.id, set);
    }
  }

  return GSPR_IDS.map((entry) => {
    const tests = [...(testsByGspr.get(entry.id) ?? [])];
    const met = tests.some((testId) => testPassing(events, testId));
    return { id: entry.id, title: entry.title, status: met ? "met" : "unmet" };
  });
}
