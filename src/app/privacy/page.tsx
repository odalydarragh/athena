import { readFile } from "node:fs/promises";
import { join } from "node:path";

async function Legal({ file }: { file: string }) {
  const text = await readFile(join(process.cwd(), "docs/legal", file), "utf8");
  return (
    <main className="wrap">
      <pre style={{ whiteSpace: "pre-wrap", fontFamily: "var(--sans)" }}>{text}</pre>
    </main>
  );
}

export default function PrivacyPage() {
  return <Legal file="privacy-policy.md" />;
}
