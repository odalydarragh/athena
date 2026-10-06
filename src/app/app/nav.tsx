import Link from "next/link";
import { logoutAction } from "../login/actions";
import type { User } from "../../lib/types";

const LINKS = [
  ["/app", "Overview"],
  ["/app/matrix", "IEC 62304"],
  ["/app/risks", "ISO 14971"],
  ["/app/gspr", "MDR GSPR"],
  ["/app/ai-act", "AI Act"],
  ["/app/export", "Export"],
  ["/app/privacy", "Privacy"],
] as const;

export function AppNav({ user }: { user: User }) {
  return (
    <>
      <nav className="top">
        <strong>DocuMDR</strong>
        <div>
          <span className="mono">
            {user.email} · {user.role}
          </span>
          <form action={logoutAction} style={{ display: "inline" }}>
            <button type="submit" className="secondary" style={{ marginLeft: "1rem" }}>
              Sign out
            </button>
          </form>
        </div>
      </nav>
      <div className="wrap">
        <nav className="subnav">
          {LINKS.map(([href, label]) => (
            <Link key={href} href={href}>
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </>
  );
}
