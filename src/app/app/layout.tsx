import type { ReactNode } from "react";
import { requireUser } from "../../lib/session";
import { AppNav } from "./nav";

export default async function AppLayout({ children }: { children: ReactNode }) {
  const user = await requireUser();
  return (
    <>
      <AppNav user={user} />
      {children}
    </>
  );
}
