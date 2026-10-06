import { requireUser } from "../../../lib/session";
import { getStore } from "../../../lib/server-store";
import { buildMatrix } from "../../../lib/iec62304/traceability";

export default async function MatrixPage() {
  const user = await requireUser();
  const store = getStore();
  const org = store.getOrg(user.organizationId);
  const rows = buildMatrix(store.getItems(org.id), org.iec62304Class, store.listEvents(org.id));

  return (
    <main className="wrap">
      <h1>IEC 62304 traceability</h1>
      <p>Class {org.iec62304Class}. Coverage is computed from co-occurring tags and latest test summaries.</p>
      <table>
        <thead>
          <tr>
            <th>REQ</th>
            <th>ARCH</th>
            <th>UNIT</th>
            <th>TEST</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.reqId}>
              <td className="mono">{row.reqId}</td>
              <td className="mono">{row.archIds.join(", ") || "—"}</td>
              <td className="mono">{row.unitIds.join(", ") || "—"}</td>
              <td className="mono">{row.testIds.join(", ") || "—"}</td>
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
