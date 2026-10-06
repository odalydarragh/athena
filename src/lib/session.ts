import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getStore } from "./server-store";
import type { User } from "./types";

export const COOKIE_NAME = "documdr_session";

export async function getSessionUser(): Promise<User | null> {
  const jar = await cookies();
  const id = jar.get(COOKIE_NAME)?.value;
  if (!id) return null;
  const store = getStore();
  return store.getUser(id) ?? store.getUserByEmail(id) ?? null;
}

export async function requireUser(): Promise<User> {
  const user = await getSessionUser();
  if (!user) redirect("/login");
  return user;
}

export async function setSession(userId: string): Promise<void> {
  const jar = await cookies();
  jar.set(COOKIE_NAME, userId, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge: 60 * 60 * 24 * 7,
  });
}

export async function clearSession(): Promise<void> {
  const jar = await cookies();
  jar.delete(COOKIE_NAME);
}
