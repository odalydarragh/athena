"use server";

import { redirect } from "next/navigation";
import { getStore } from "../../lib/server-store";
import { clearSession, setSession } from "../../lib/session";

export async function loginAction(formData: FormData): Promise<void> {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  if (process.env.DEMO_MODE === "false") {
    redirect("/login?error=disabled");
  }
  const user = getStore().getUserByEmail(email);
  if (!user) {
    redirect("/login?error=unknown");
  }
  await setSession(user.id);
  redirect("/app");
}

export async function logoutAction(): Promise<void> {
  await clearSession();
  redirect("/");
}
