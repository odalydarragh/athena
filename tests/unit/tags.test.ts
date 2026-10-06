import { describe, expect, it } from "vitest";
import { parseTags, TAG_RE } from "../../src/lib/parser/tags";

describe("parseTags", () => {
  it("parses mixed tags and ignores lowercase", () => {
    const tags = parseTags("see #REQ-101 and #RISK-04 and #req-nope");
    expect(tags.map((t) => t.raw)).toEqual(["#REQ-101", "#RISK-04"]);
  });

  it("parses GSPR dotted ids", () => {
    expect(parseTags("#GSPR-17.2")[0]).toEqual({
      kind: "GSPR",
      id: "17.2",
      raw: "#GSPR-17.2",
    });
  });

  it("parses MODEL and TEST compound ids", () => {
    const tags = parseTags("#MODEL-ECG-1 #TEST-UNIT-12 #SOUP-LIB-9 #CAPA-3 #AI-1 #ARCH-CORE #UNIT-ECG");
    expect(tags.map((t) => t.kind).sort()).toEqual(
      ["AI", "ARCH", "CAPA", "MODEL", "SOUP", "TEST", "UNIT"].sort(),
    );
  });

  it("exposes the spec regex", () => {
    expect(TAG_RE.source).toContain("REQ|RISK|TEST|ARCH|UNIT|GSPR|AI|SOUP|CAPA|MODEL");
  });
});
