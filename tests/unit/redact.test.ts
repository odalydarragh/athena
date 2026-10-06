import { describe, expect, it } from "vitest";
import { ForbiddenContentError } from "../../src/lib/errors";
import { assertAllowedContent, redactText } from "../../src/lib/privacy/redact";

describe("redactText", () => {
  it("replaces emails", () => {
    expect(redactText("hi qa@example.com")).toBe("hi [REDACTED_EMAIL]");
  });

  it("replaces bearer tokens", () => {
    expect(redactText("Authorization: Bearer abcdefghijklmnop")).toContain(
      "[REDACTED_SECRET]",
    );
  });

  it("replaces AWS access keys", () => {
    expect(redactText("AKIAAAAAAAAAAAAAAAAA")).toContain("[REDACTED_SECRET]");
  });

  it("replaces Irish PPS-like tokens", () => {
    expect(redactText("PPS 1234567T")).toContain("[REDACTED_PPS]");
  });

  it("replaces NHS numbers", () => {
    expect(redactText("NHS 123 456 7890")).toContain("[REDACTED_NHS]");
  });

  it("replaces private key blocks", () => {
    expect(
      redactText("-----BEGIN RSA PRIVATE KEY-----\nMIIE\n-----END RSA PRIVATE KEY-----"),
    ).toContain("[REDACTED_SECRET]");
  });

  it("replaces IBANs", () => {
    expect(redactText("pay IE64IRCE92050112345678")).toContain("[REDACTED_IBAN]");
  });
});

describe("assertAllowedContent", () => {
  it("throws on leftover clinical markers", () => {
    expect(() => assertAllowedContent("PATIENT John")).toThrow(
      ForbiddenContentError,
    );
  });

  it("throws on MRN markers", () => {
    expect(() => assertAllowedContent("MRN: 998877")).toThrow(
      ForbiddenContentError,
    );
  });

  it("throws on DOB markers", () => {
    expect(() => assertAllowedContent("DOB: 1990-01-01")).toThrow(
      ForbiddenContentError,
    );
  });

  it("allows tagged engineering messages", () => {
    expect(() => assertAllowedContent("#REQ-101 add alarm")).not.toThrow();
  });
});
