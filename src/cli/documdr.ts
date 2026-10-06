import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { ForbiddenContentError } from "../lib/errors";
import { parseTags, type ParsedTag } from "../lib/parser/tags";
import { assertAllowedContent, redactText } from "../lib/privacy/redact";

export type CommitMetadata = {
  message: string;
  tags: ParsedTag[];
  paths: string[];
};

export function parseCommitMessage(message: string, paths: string[] = []): CommitMetadata {
  const redacted = redactText(message);
  assertAllowedContent(redacted);
  return {
    message: redacted,
    tags: parseTags(redacted),
    paths: paths.slice(0, 200),
  };
}

export async function runCli(
  argv: string[],
  io: { log: (line: string) => void; error: (line: string) => void } = {
    log: (line) => console.log(line),
    error: (line) => console.error(line),
  },
): Promise<number> {
  const [command, ...rest] = argv;
  if (command !== "parse") {
    io.error("Usage: documdr parse --message <file> [--paths p1,p2]");
    return 1;
  }
  const msgIdx = rest.indexOf("--message");
  if (msgIdx < 0 || !rest[msgIdx + 1]) {
    io.error("Missing --message <file>");
    return 1;
  }
  const pathsIdx = rest.indexOf("--paths");
  const paths = pathsIdx >= 0 && rest[pathsIdx + 1] ? rest[pathsIdx + 1].split(",").filter(Boolean) : [];
  try {
    const text = await readFile(rest[msgIdx + 1], "utf8");
    const metadata = parseCommitMessage(text, paths);
    io.log(JSON.stringify(metadata, null, 2));
    return 0;
  } catch (error) {
    if (error instanceof ForbiddenContentError) {
      io.error(error.message);
      return 2;
    }
    io.error(error instanceof Error ? error.message : "parse failed");
    return 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  void runCli(args).then((code) => {
    process.exitCode = code;
  });
}
