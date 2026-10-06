import { describe, expect, it } from "vitest";
import {
  isUnacceptable,
  parseRiskFields,
  rpn,
  upsertRisks,
  verifyRiskControl,
} from "../../src/lib/iso14971/fmea";
import type { GitEvent, RiskRow } from "../../src/lib/types";

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

describe("parseRiskFields", () => {
  it("reads structured S P D hazard harm control", () => {
    expect(
      parseRiskFields("S:4 P:2 D:3 HAZARD:over-infusion HARM:injury CONTROL:hard-limit"),
    ).toEqual({
      severity: 4,
      probability: 2,
      detectability: 3,
      hazard: "over-infusion",
      harm: "injury",
      control: "hard-limit",
    });
  });
});

describe("upsertRisks", () => {
  it("defaults new risks to 3/3/3 and RPN 27", () => {
    const rows = upsertRisks([], event({ sha: "s1", message: "#RISK-04 #REQ-101 new hazard" }));
    expect(rows[0]).toMatchObject({
      id: "RISK-04",
      severity: 3,
      probability: 3,
      detectability: 3,
      rpn: 27,
      controlsVerified: false,
      changePrompt: false,
      linkedItemIds: ["REQ-101"],
    });
  });

  it("sets changePrompt and increments probability once per sha when linked item changes", () => {
    let rows = upsertRisks(
      [],
      event({ sha: "s1", message: "#RISK-04 #REQ-101 S:3 P:2 D:2", paths: ["src/alarm.ts"] }),
    );
    rows = upsertRisks(
      rows,
      event({ sha: "s2", message: "#RISK-04 #REQ-101 tweak", paths: ["src/alarm.ts"] }),
    );
    expect(rows[0].changePrompt).toBe(true);
    expect(rows[0].controlsVerified).toBe(false);
    expect(rows[0].probability).toBe(3);
    rows = upsertRisks(
      rows,
      event({ sha: "s2", message: "#RISK-04 #REQ-101 tweak again", paths: ["src/alarm.ts"] }),
    );
    expect(rows[0].probability).toBe(3);
  });
});

describe("verifyRiskControl", () => {
  it("clears changePrompt without lowering probability", () => {
    const start: RiskRow[] = [
      {
        id: "RISK-04",
        hazard: "h",
        sequence: "",
        harm: "harm",
        severity: 4,
        probability: 4,
        detectability: 3,
        rpn: 48,
        linkedItemIds: ["REQ-101"],
        controls: ["limit"],
        controlsVerified: false,
        changePrompt: true,
        probabilityBumpShas: ["s2"],
        paths: [],
      },
    ];
    const rows = verifyRiskControl(start, "RISK-04");
    expect(rows[0].controlsVerified).toBe(true);
    expect(rows[0].changePrompt).toBe(false);
    expect(rows[0].probability).toBe(4);
    expect(isUnacceptable(rows[0])).toBe(false);
  });
});

describe("rpn", () => {
  it("multiplies S P D", () => {
    expect(rpn({ severity: 5, probability: 2, detectability: 4 })).toBe(40);
  });
});
