import { requireUser } from "../../../lib/session";
import { getStore } from "../../../lib/server-store";
import { assertEntitlement } from "../../../lib/billing/entitlements";
import { isUnacceptable, rpn } from "../../../lib/iso14971/fmea";
import { verifyRiskAction } from "../export/actions";

export default async function RisksPage() {
  const user = await requireUser();
  const store = getStore();
  const org = store.getOrg(user.organizationId);
  try {
    assertEntitlement(org, "viewFmea");
  } catch (error) {
    return (
      <main className="wrap">
        <h1>ISO 14971 FMEA</h1>
        <p className="flash">{error instanceof Error ? error.message : "Upgrade required"}</p>
      </main>
    );
  }
  const rows = store.getRisks(org.id);

  return (
    <main className="wrap">
      <h1>ISO 14971 FMEA</h1>
      <p>Linked hazard tags. A code change on a linked item sets a change prompt until a quality reviewer re-verifies controls.</p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Hazard</th>
            <th>S/P/D</th>
            <th>RPN</th>
            <th>Prompt</th>
            <th>Verified</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td className="mono">{row.id}</td>
              <td>{row.hazard}</td>
              <td className="mono">
                {row.severity}/{row.probability}/{row.detectability}
              </td>
              <td>
                {rpn(row)}
                {isUnacceptable(row) ? " · unacceptable" : ""}
              </td>
              <td>{row.changePrompt ? "yes" : "no"}</td>
              <td>
                {row.controlsVerified ? "yes" : "no"}
                {user.role === "quality" && !row.controlsVerified ? (
                  <form action={verifyRiskAction}>
                    <input type="hidden" name="riskId" value={row.id} />
                    <button type="submit">Verify control</button>
                  </form>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
