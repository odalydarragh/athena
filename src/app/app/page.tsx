import { requireUser } from "../../lib/session";
import { getStore } from "../../lib/server-store";
import { setClassAction } from "./export/actions";
import { buildMatrix } from "../../lib/iec62304/traceability";

export default async function AppHome() {
  const user = await requireUser();
  const store = getStore();
  const org = store.getOrg(user.organizationId);
  const events = store.listEvents(org.id);
  const matrix = buildMatrix(store.getItems(org.id), org.iec62304Class, events);
  const covered = matrix.filter((row) => row.status === "covered").length;

  return (
    <main className="wrap">
      <h1>{org.name}</h1>
      <p className="lede">
        Simulated repository <code>{events[0]?.repository ?? "galway/samd-demo"}</code>. Profile: EU
        MDR Class {org.mdrClass} Rule {org.rule}, IEC 62304 Class {org.iec62304Class}, tier{" "}
        {org.tier}. Metadata only — no source blobs stored.
      </p>
      <div className="grid">
        <article className="card">
          <h3>Traceability</h3>
          <p>
            {covered}/{matrix.length} requirements covered
          </p>
        </article>
        <article className="card">
          <h3>Events</h3>
          <p>{events.length} git metadata events</p>
        </article>
        <article className="card">
          <h3>Safety class</h3>
          <form action={setClassAction}>
            <select name="safetyClass" defaultValue={org.iec62304Class}>
              <option value="A">Class A</option>
              <option value="B">Class B</option>
              <option value="C">Class C</option>
            </select>
            <p>
              <button type="submit">Update class</button>
            </p>
          </form>
        </article>
      </div>
    </main>
  );
}
