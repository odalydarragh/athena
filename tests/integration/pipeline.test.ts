import { describe, expect, it } from "vitest";
import { MemoryStore } from "../../src/lib/store/memory";
import { seedDemo } from "../../src/lib/store/seed";
import { ingestGitEvent } from "../../src/lib/ingest/events";
import { buildMatrix } from "../../src/lib/iec62304/traceability";
import { signTechnicalFile } from "../../src/lib/hitl/signature";
import { exportTechnicalFile } from "../../src/lib/compile/technical-file";
import { createDsarExport, eraseUser } from "../../src/lib/gdpr/dsar";
import { ExportBlockedError } from "../../src/lib/errors";
import { DISCLAIMER } from "../../src/lib/types";

describe("end-to-end pipeline", () => {
  it("seeds, ingests, blocks unsigned export, then exports after HITL", () => {
    const store = new MemoryStore();
    seedDemo(store);

    ingestGitEvent(store, {
      id: "evt-extra",
      organizationId: "galway-demo",
      repository: "galway/samd-demo",
      sha: "dd40404",
      at: "2026-10-03T12:00:00.000Z",
      authorLogin: "eng",
      paths: ["src/alarm.ts"],
      message: "#RISK-04 #REQ-101 follow-up change",
    });

    const matrix = buildMatrix(
      store.getItems("galway-demo"),
      store.getOrg("galway-demo").iec62304Class,
      store.listEvents("galway-demo"),
    );
    expect(matrix.find((row) => row.reqId === "REQ-101")?.status).toBe("covered");
    expect(store.getRisks("galway-demo").find((r) => r.id === "RISK-04")?.changePrompt).toBe(true);
    expect(
      store.listEvents("galway-demo").some((event) => event.message.includes("#GSPR-17.2")),
    ).toBe(true);

    expect(() => exportTechnicalFile(store, "galway-demo")).toThrow(ExportBlockedError);

    const qa = store.getUserByEmail("qa@example.com")!;
    signTechnicalFile(store, {
      orgId: "galway-demo",
      userId: qa.id,
      shaScope: store.latestSha("galway-demo")!,
      userAgent: "integration",
    });
    const exported = exportTechnicalFile(store, "galway-demo");
    expect(exported.disclaimer).toBe(DISCLAIMER);
    expect(exported.gspr.find((g) => g.id === "17.2")?.status).toBe("met");

    const eng = store.getUserByEmail("eng@example.com")!;
    const dsar = createDsarExport(store, eng.id) as { events: unknown[] };
    expect(dsar.events.length).toBeGreaterThan(0);
    eraseUser(store, eng.id);
    expect(store.getUserByEmail("eng@example.com")).toBeUndefined();
  });
});
