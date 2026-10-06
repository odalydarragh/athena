import { requireUser } from "../../../lib/session";
import { getStore } from "../../../lib/server-store";
import { assertEntitlement } from "../../../lib/billing/entitlements";
import { evaluateGspr } from "../../../lib/mdr/gspr";

export default async function GsprPage() {
  const user = await requireUser();
  const store = getStore();
  const org = store.getOrg(user.organizationId);
  try {
    assertEntitlement(org, "viewGspr");
  } catch (error) {
    return (
      <main className="wrap">
        <h1>EU MDR GSPR</h1>
        <p className="flash">{error instanceof Error ? error.message : "Upgrade required"}</p>
      </main>
    );
  }
  const rows = evaluateGspr(store.listEvents(org.id));

  return (
    <main className="wrap">
      <h1>EU MDR Annex I GSPR (software-relevant)</h1>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td className="mono">{row.id}</td>
              <td>{row.title}</td>
              <td>
                <span className={`pill ${row.status}`}>{row.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
