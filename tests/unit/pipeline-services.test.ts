import { createHash, randomUUID } from "node:crypto";
import { describe, expect, it } from "vitest";
import { ingestGitEvent } from "../../src/lib/ingest/events";
import { MemoryStore } from "../../src/lib/store/memory";
import { seedDemo } from "../../src/lib/store/seed";
import {
  ExportBlockedError,
  ForbiddenContentError,
  SeatLimitError,
  UpgradeRequiredError,
} from "../../src/lib/errors";
import { assertEntitlement, contributorCount } from "../../src/lib/billing/entitlements";
import { signTechnicalFile } from "../../src/lib/hitl/signature";
import { compileTechnicalFile, exportTechnicalFile } from "../../src/lib/compile/technical-file";
import { createDsarExport, eraseUser } from "../../src/lib/gdpr/dsar";
import { DISCLAIMER, SIGNATURE_MEANING, type GitEvent } from "../../src/lib/types";

function gitEvent(store: MemoryStore, partial: Partial<GitEvent> & { message: string; sha: string }): GitEvent {
  const organizationId = partial.organizationId ?? "galway-demo";
  return {
    id: randomUUID(),
    organizationId,
    repository: "galway/samd-demo",
    at: new Date().toISOString(),
    authorLogin: "eng",
    paths: ["src/alarm.ts"],
    ...partial,
  };
}

describe("ingestGitEvent", () => {
  it("redacts emails and rejects clinical content", () => {
    const store = new MemoryStore();
    seedDemo(store);
    ingestGitEvent(
      store,
      gitEvent(store, {
        sha: "c0ffee1",
        message: "#REQ-101 ping qa@example.com",
        testSummary: { passed: 1, failed: 0, skipped: 0 },
      }),
    );
    const stored = store.listEvents("galway-demo").find((e) => e.sha === "c0ffee1");
    expect(stored?.message).toContain("[REDACTED_EMAIL]");
    expect(stored?.message).not.toContain("@example.com");
    expect(() =>
      ingestGitEvent(store, gitEvent(store, { sha: "bad0001", message: "PATIENT record #REQ-101" })),
    ).toThrow(ForbiddenContentError);
  });
});

describe("entitlements", () => {
  it("blocks a fourth distinct author on the free tier", () => {
    const store = new MemoryStore();
    store.putOrg({
      id: "free-1",
      name: "Spinout",
      tier: "free",
      iec62304Class: "A",
      mdrClass: "IIa",
      rule: "11",
      modules: { aiAct: false },
      invitedUserIds: [],
    });
    for (const [i, login] of ["a", "b", "c"].entries()) {
      ingestGitEvent(
        store,
        gitEvent(store, {
          organizationId: "free-1",
          sha: `aaa000${i}`,
          authorLogin: login,
          message: "#REQ-1 #TEST-1",
          testSummary: { passed: 1, failed: 0, skipped: 0 },
        }),
      );
    }
    expect(contributorCount(store, "free-1")).toBe(3);
    expect(() =>
      ingestGitEvent(
        store,
        gitEvent(store, {
          organizationId: "free-1",
          sha: "aaa0003",
          authorLogin: "d",
          message: "#REQ-1",
        }),
      ),
    ).toThrow(SeatLimitError);
    expect(() => assertEntitlement(store.getOrg("free-1"), "export")).toThrow(UpgradeRequiredError);
    expect(() => assertEntitlement(store.getOrg("free-1"), "viewFmea")).toThrow(UpgradeRequiredError);
  });
});

describe("HITL and export", () => {
  it("lets only quality sign and requires a matching shaScope", () => {
    const store = new MemoryStore();
    seedDemo(store);
    const eng = store.getUserByEmail("eng@example.com")!;
    const qa = store.getUserByEmail("qa@example.com")!;
    expect(() =>
      signTechnicalFile(store, {
        orgId: "galway-demo",
        userId: eng.id,
        shaScope: "nope",
        userAgent: "vitest",
      }),
    ).toThrow(/quality/i);

    const compiled = compileTechnicalFile(store, "galway-demo");
    expect(compiled.disclaimer).toBe(DISCLAIMER);
    expect(() => exportTechnicalFile(store, "galway-demo")).toThrow(ExportBlockedError);

    const head = store.latestSha("galway-demo")!;
    const sig = signTechnicalFile(store, {
      orgId: "galway-demo",
      userId: qa.id,
      shaScope: head,
      userAgent: "vitest",
    });
    expect(sig.meaning).toBe(SIGNATURE_MEANING);
    expect(sig.signerRole).toBe("quality");
    const exported = exportTechnicalFile(store, "galway-demo");
    expect(exported.gspr.some((g) => g.id === "17.2" && g.status === "met")).toBe(true);
    expect(exported.disclaimer).toBe(DISCLAIMER);
  });
});

describe("GDPR DSAR", () => {
  it("exports then minimises a user", () => {
    const store = new MemoryStore();
    seedDemo(store);
    const eng = store.getUserByEmail("eng@example.com")!;
    const dsar = createDsarExport(store, eng.id);
    expect(JSON.stringify(dsar)).toContain("eng@example.com");
    eraseUser(store, eng.id);
    expect(store.getUserByEmail("eng@example.com")).toBeUndefined();
    const hash = createHash("sha256").update(eng.id).digest("hex").slice(0, 12);
    expect(store.listEvents("galway-demo").every((e) => e.authorLogin !== "eng")).toBe(true);
    expect(store.listEvents("galway-demo").some((e) => e.authorLogin === `erased-${hash}`)).toBe(true);
  });
});
