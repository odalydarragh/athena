import { describe, expect, it } from "vitest";
import {
  DocuMdrError,
  ExportBlockedError,
  ForbiddenContentError,
  NotFoundError,
  SeatLimitError,
  UpgradeRequiredError,
} from "../../src/lib/errors";

describe("DocuMdrError", () => {
  it("ForbiddenContentError uses code FORBIDDEN_CONTENT", () => {
    const err = new ForbiddenContentError("patient data");
    expect(err).toBeInstanceOf(DocuMdrError);
    expect(err.code).toBe("FORBIDDEN_CONTENT");
    expect(err.message).toContain("patient data");
  });

  it("ExportBlockedError uses code EXPORT_BLOCKED", () => {
    expect(new ExportBlockedError("unsigned").code).toBe("EXPORT_BLOCKED");
  });

  it("UpgradeRequiredError uses code UPGRADE_REQUIRED", () => {
    expect(new UpgradeRequiredError("free").code).toBe("UPGRADE_REQUIRED");
  });

  it("SeatLimitError uses code SEAT_LIMIT", () => {
    expect(new SeatLimitError("limit").code).toBe("SEAT_LIMIT");
  });

  it("NotFoundError uses code NOT_FOUND", () => {
    expect(new NotFoundError("missing").code).toBe("NOT_FOUND");
  });
});
