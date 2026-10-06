import { describe, expect, it } from "vitest";
import { compileAnnexIv } from "../../src/lib/aiact/annex-iv";
import type { GitEvent } from "../../src/lib/types";

function event(partial: Partial<GitEvent> & { message: string; sha: string }): GitEvent {
  return {
    id: partial.sha,
    organizationId: "galway-demo",
    repository: "galway/samd-demo",
    at: "2026-10-01T10:00:00.000Z",
    authorLogin: "eng",
    paths: ["models/ecg.py"],
    ...partial,
  };
}

describe("compileAnnexIv", () => {
  it("emits nine Annex IV sections and never signs the DoC", () => {
    const file = compileAnnexIv({
      providerName: "Galway Demo Ltd",
      events: [
        event({
          sha: "abc9999",
          message:
            "#MODEL-ECG-1 PURPOSE:rhythm-triage METRIC:auroc=0.91 BIAS:age-band OVERSIGHT:cardiologist DATASET:deidentified-summary-only",
        }),
      ],
      risks: [],
    });
    expect(file.sections).toHaveLength(9);
    expect(file.sections.map((s) => s.number)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9]);
    const doc = file.sections.find((s) => s.number === 8);
    expect(doc?.status).toBe("not-signed");
    expect(file.sections[8].body).toMatch(/Incident reporting is performed by the manufacturer, not DocuMDR/);
    expect(file.sections[0].body).toContain("Galway Demo Ltd");
    expect(file.sections[0].body).toContain("abc9999");
    expect(file.sections[0].body).toContain("rhythm-triage");
  });

  it("truncates DATASET values to 200 characters", () => {
    const long = "x".repeat(250);
    const file = compileAnnexIv({
      providerName: "Galway Demo Ltd",
      events: [event({ sha: "s1", message: `#MODEL-ECG-1 DATASET:${long}` })],
      risks: [],
    });
    expect(file.sections[1].body).not.toContain("x".repeat(201));
  });
});
