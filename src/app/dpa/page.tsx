import { readFile } from "node:fs/promises";
import { join } from "node:path";

export default async function DpaPage() {
  const text = await readFile(join(process.cwd(), "docs/legal/dpa.md"), "utf8");
  return (
    <main className="wrap">
      <pre style={{ whiteSpace: "pre-wrap", fontFamily: "var(--sans)" }}>{text}</pre>
    </main>
  );
}
