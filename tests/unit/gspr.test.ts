import { describe, expect, it } from "vitest";
import { evaluateGspr, GSPR_IDS } from "../../src/lib/mdr/gspr";
import type { GitEvent } from "../../src/lib/types";

function event(partial: Partial<GitEvent> & { message: string; sha: string }): GitEvent {
  return {
    id: partial.sha,
    organizationId: "galway-demo",
    repository: "galway/samd-demo",
    at: "2026-10-01T10:00:00.000Z",
    authorLogin: "eng",
    paths: ["src/alarm.ts"],
    ...partial,
  };
}

describe("evaluateGspr", () => {
  it("exposes the canonical software-relevant GSPR ids", () => {
    expect(GSPR_IDS.map((g) => g.id)).toEqual([
      "1",
      "2",
      "3",
      "4",
      "5",
      "14.2",
      "17.1",
      "17.2",
      "17.3",
      "17.4",
      "22",
      "23.1",
    ]);
  });

  it("marks a GSPR met only with a co-occurring passing TEST", () => {
    const rows = evaluateGspr([
      event({
        sha: "s1",
        message: "#GSPR-17.2 #TEST-UI lifecycle",
        testSummary: { passed: 4, failed: 0, skipped: 0 },
      }),
      event({
        sha: "s2",
        message: "#GSPR-17.3 no test",
      }),
    ]);
    expect(rows.find((r) => r.id === "17.2")?.status).toBe("met");
    expect(rows.find((r) => r.id === "17.3")?.status).toBe("unmet");
    expect(rows.find((r) => r.id === "1")?.status).toBe("unmet");
  });

  it("stays unmet when the latest co-occurring test failed", () => {
    const rows = evaluateGspr([
      event({
        sha: "s1",
        at: "2026-10-01T10:00:00.000Z",
        message: "#GSPR-17.1 #TEST-UI",
        testSummary: { passed: 1, failed: 0, skipped: 0 },
      }),
      event({
        sha: "s2",
        at: "2026-10-02T10:00:00.000Z",
        message: "#TEST-UI",
        testSummary: { passed: 0, failed: 1, skipped: 0 },
      }),
    ]);
    expect(rows.find((r) => r.id === "17.1")?.status).toBe("unmet");
  });
});
