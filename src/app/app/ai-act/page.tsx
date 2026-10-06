import { requireUser } from "../../../lib/session";
import { getStore } from "../../../lib/server-store";
import { assertEntitlement } from "../../../lib/billing/entitlements";
import { compileAnnexIv } from "../../../lib/aiact/annex-iv";

export default async function AiActPage() {
  const user = await requireUser();
  const store = getStore();
  const org = store.getOrg(user.organizationId);
  try {
    assertEntitlement(org, "viewAnnexIv");
  } catch {
    return (
      <main className="wrap">
        <h1>EU AI Act Annex IV</h1>
        <p className="flash">Annex IV requires the AI Governance tier (€799/month).</p>
        <p>The demo organisation is on Team, so this module stays locked — as it would for a €249 subscriber.</p>
      </main>
    );
  }
  const file = compileAnnexIv({
    providerName: org.name,
    events: store.listEvents(org.id),
    risks: store.getRisks(org.id),
  });

  return (
    <main className="wrap">
      <h1>EU AI Act Annex IV</h1>
      {file.sections.map((section) => (
        <article className="card" key={section.number} style={{ marginBottom: "0.75rem" }}>
          <h3>
            {section.number}. {section.title}{" "}
            {section.status ? <span className="pill unmet">{section.status}</span> : null}
          </h3>
          <p>{section.body}</p>
        </article>
      ))}
    </main>
  );
}
