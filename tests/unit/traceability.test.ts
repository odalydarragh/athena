import { describe, expect, it } from "vitest";
import { buildMatrix, buildSoftwareItems } from "../../src/lib/iec62304/traceability";
import type { GitEvent } from "../../src/lib/types";

function event(partial: Partial<GitEvent> & { message: string; sha: string }): GitEvent {
  return {
    id: partial.id ?? partial.sha,
    organizationId: "galway-demo",
    repository: "galway/samd-demo",
    at: "2026-10-01T10:00:00.000Z",
    authorLogin: "eng",
    paths: ["src/alarm.ts"],
    ...partial,
  };
}

describe("buildSoftwareItems", () => {
  it("links co-occurring tags and records shas", () => {
    const items = buildSoftwareItems(
      [
        event({
          sha: "aaa1111",
          message: "#REQ-101 #ARCH-CORE alarm limit #TEST-UI",
          testSummary: { passed: 3, failed: 0, skipped: 0 },
        }),
      ],
      "B",
    );
    const req = items.find((i) => i.id === "REQ-101");
    expect(req?.kind).toBe("REQ");
    expect(req?.linkedIds.sort()).toEqual(["ARCH-CORE", "TEST-UI"]);
    expect(req?.shas).toEqual(["aaa1111"]);
  });
});

describe("buildMatrix", () => {
  it("marks class A covered when tests pass", () => {
    const events = [
      event({
        sha: "aaa1111",
        message: "#REQ-101 #TEST-UI",
        testSummary: { passed: 1, failed: 0, skipped: 0 },
      }),
    ];
    const items = buildSoftwareItems(events, "A");
    expect(buildMatrix(items, "A", events)[0].status).toBe("covered");
  });

  it("marks class B gap when ARCH is missing", () => {
    const events = [
      event({
        sha: "aaa1111",
        message: "#REQ-101 #TEST-UI",
        testSummary: { passed: 1, failed: 0, skipped: 0 },
      }),
    ];
    const items = buildSoftwareItems(events, "B");
    expect(buildMatrix(items, "B", events)[0].status).toBe("gap");
  });

  it("marks class C partial when UNIT is missing but ARCH and TEST exist", () => {
    const events = [
      event({
        sha: "aaa1111",
        message: "#REQ-101 #ARCH-CORE #TEST-UI",
        testSummary: { passed: 1, failed: 0, skipped: 0 },
      }),
    ];
    const items = buildSoftwareItems(events, "C");
    const row = buildMatrix(items, "C", events)[0];
    expect(row.status).toBe("partial");
    expect(row.archIds).toEqual(["ARCH-CORE"]);
    expect(row.unitIds).toEqual([]);
  });

  it("marks partial when latest test failed", () => {
    const events = [
      event({
        sha: "aaa1111",
        message: "#REQ-101 #ARCH-CORE #TEST-UI",
        testSummary: { passed: 0, failed: 2, skipped: 0 },
      }),
    ];
    const items = buildSoftwareItems(events, "B");
    expect(buildMatrix(items, "B", events)[0].status).toBe("partial");
  });

  it("sorts requirement rows by id", () => {
    const events = [
      event({ sha: "b", message: "#REQ-200 #TEST-Z", testSummary: { passed: 1, failed: 0, skipped: 0 } }),
      event({ sha: "a", message: "#REQ-101 #TEST-A", testSummary: { passed: 1, failed: 0, skipped: 0 } }),
    ];
    const items = buildSoftwareItems(events, "A");
    expect(buildMatrix(items, "A", events).map((r) => r.reqId)).toEqual([
      "REQ-101",
      "REQ-200",
    ]);
  });
});
