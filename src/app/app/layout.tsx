import type { ReactNode } from "react";
import { requireUser } from "../../lib/session";
import { AppNav } from "./nav";

export const dynamic = "force-dynamic";

export default async function AppLayout({ children }: { children: ReactNode }) {
  const user = await requireUser();
  return (
    <>
      <AppNav user={user} />
      {children}
    </>
  );
}
  const user = await requireUser();
  return (
    <>
      <AppNav user={user} />
      {children}
    </>
  );
}
