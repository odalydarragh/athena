import { requireUser } from "../../../lib/session";
import { getStore } from "../../../lib/server-store";
import { compileTechnicalFile } from "../../../lib/compile/technical-file";
import { signExportAction } from "./actions";
import { DISCLAIMER } from "../../../lib/types";

export default async function ExportPage() {
  const user = await requireUser();
  const store = getStore();
  const compiled = compileTechnicalFile(store, user.organizationId);
  const head = compiled.headSha;
  const signed = compiled.signatures.some((s) => s.shaScope === head);

  return (
    <main className="wrap">
      <h1>Technical File export</h1>
      <p className="banner">{DISCLAIMER}</p>
      <p>
        HEAD SHA: <code>{head ?? "none"}</code> · Signed: {signed ? "yes" : "no"} · Role: {user.role}
      </p>
      {user.role !== "quality" ? (
        <p className="flash">Only a quality reviewer may apply the electronic signature (simple eIDAS signature, not qualified).</p>
      ) : (
        <form action={signExportAction}>
          <button type="submit">Sign current HEAD</button>
        </form>
      )}
      {signed ? (
        <p>
          <a className="btn" href="/app/export/download">
            Download JSON
          </a>
        </p>
      ) : (
        <p className="flash">Export is blocked until a quality signature matches this SHA.</p>
      )}
    </main>
  );
}
