import { readFile } from "node:fs/promises";
import { join } from "node:path";

export default async function CookiesPage() {
  const text = await readFile(join(process.cwd(), "docs/legal/cookie-policy.md"), "utf8");
  return (
    <main className="wrap">
      <pre style={{ whiteSpace: "pre-wrap", fontFamily: "var(--sans)" }}>{text}</pre>
    </main>
  );
}
