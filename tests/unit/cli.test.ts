import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { parseCommitMessage, runCli } from "../../src/cli/documdr";

describe("parseCommitMessage", () => {
  it("returns redacted metadata and tags without file bodies", () => {
    const result = parseCommitMessage("#REQ-101 ping qa@example.com", ["src/a.ts"]);
    expect(result.message).toContain("[REDACTED_EMAIL]");
    expect(result.tags.map((t) => t.raw)).toEqual(["#REQ-101"]);
    expect(result.paths).toEqual(["src/a.ts"]);
    expect(result).not.toHaveProperty("source");
  });

  it("throws ForbiddenContentError on clinical markers", () => {
    expect(() => parseCommitMessage("PATIENT #REQ-101")).toThrow(/FORBIDDEN_CONTENT|patient/i);
  });
});

describe("runCli", () => {
  it("prints JSON for parse --message", async () => {
    const dir = await mkdtemp(join(tmpdir(), "documdr-"));
    const file = join(dir, "msg.txt");
    await writeFile(file, "#RISK-04 hazard note", "utf8");
    const logs: string[] = [];
    const code = await runCli(["parse", "--message", file], {
      log: (line) => logs.push(line),
      error: () => undefined,
    });
    expect(code).toBe(0);
    const parsed = JSON.parse(logs.join(""));
    expect(parsed.tags[0].raw).toBe("#RISK-04");
  });

  it("exits 2 on forbidden content", async () => {
    const dir = await mkdtemp(join(tmpdir(), "documdr-"));
    const file = join(dir, "msg.txt");
    await writeFile(file, "MRN: 12 #REQ-1", "utf8");
    const code = await runCli(["parse", "--message", file], {
      log: () => undefined,
      error: () => undefined,
    });
    expect(code).toBe(2);
  });
});
