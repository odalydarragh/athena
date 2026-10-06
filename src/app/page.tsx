import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <nav className="top">
        <strong>DocuMDR</strong>
        <div>
          <Link href="/privacy">Privacy</Link>
          <Link href="/login">Sign in</Link>
        </div>
      </nav>
      <main className="wrap">
        <p className="banner">
          DocuMDR compiles draft technical documentation from software-development metadata. It is
          not a notified body, does not issue CE marking, does not provide legal or regulatory
          advice, and is not itself a medical device.
        </p>
        <section className="hero">
          <h1>Regulatory files that compile from git.</h1>
          <p className="lede">
            Built for SaMD teams in Galway and across the EU. DocuMDR sits behind your commits,
            parses <code>#REQ</code>, <code>#RISK</code>, <code>#TEST</code> and <code>#MODEL</code>{" "}
            tags, and keeps IEC 62304, ISO 14971, EU MDR GSPR, and EU AI Act Annex IV drafts
            audit-ready — without shipping source code or patient data off the machine.
          </p>
          <p>
            <Link className="btn" href="/login">
              Open the Galway demo
            </Link>
          </p>
        </section>
        <h2>Pricing</h2>
        <div className="grid">
          <article className="card">
            <h3>Free</h3>
            <p className="price">€0</p>
            <p>3 contributors. IEC 62304 matrix preview. No Technical File export.</p>
          </article>
          <article className="card">
            <h3>Team</h3>
            <p className="price">€249<span className="mono">/mo</span></p>
            <p>25 seats. ISO 14971 FMEA + MDR GSPR + HITL export.</p>
          </article>
          <article className="card">
            <h3>AI Governance</h3>
            <p className="price">€799<span className="mono">/mo</span></p>
            <p>100 seats. EU AI Act Annex IV + notified-body export package.</p>
          </article>
        </div>
      </main>
    </>
  );
}
