"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { assertEntitlement } from "../../../lib/billing/entitlements";
import { exportTechnicalFile } from "../../../lib/compile/technical-file";
import { createDsarExport, eraseUser } from "../../../lib/gdpr/dsar";
import { signTechnicalFile } from "../../../lib/hitl/signature";
import { verifyRiskControl } from "../../../lib/iso14971/fmea";
import { requireUser, clearSession } from "../../../lib/session";
import { getStore } from "../../../lib/server-store";
import type { SafetyClass } from "../../../lib/types";

export async function signExportAction(): Promise<void> {
  const user = await requireUser();
  const store = getStore();
  const head = store.latestSha(user.organizationId);
  if (!head) return;
  signTechnicalFile(store, {
    orgId: user.organizationId,
    userId: user.id,
    shaScope: head,
    userAgent: "documdr-web",
  });
  revalidatePath("/app/export");
}

export async function exportJsonAction(): Promise<{ error?: string; json?: string }> {
  const user = await requireUser();
  const store = getStore();
  try {
    assertEntitlement(store.getOrg(user.organizationId), "export");
    const file = exportTechnicalFile(store, user.organizationId);
    return { json: JSON.stringify(file, null, 2) };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "Export failed" };
  }
}

export async function verifyRiskAction(formData: FormData): Promise<void> {
  const user = await requireUser();
  if (user.role !== "quality") return;
  const id = String(formData.get("riskId") ?? "");
  const store = getStore();
  store.setRisks(user.organizationId, verifyRiskControl(store.getRisks(user.organizationId), id));
  revalidatePath("/app/risks");
}

export async function setClassAction(formData: FormData): Promise<void> {
  const user = await requireUser();
  const next = String(formData.get("safetyClass")) as SafetyClass;
  if (!["A", "B", "C"].includes(next)) return;
  const store = getStore();
  const org = store.getOrg(user.organizationId);
  store.putOrg({ ...org, iec62304Class: next });
  revalidatePath("/app");
  revalidatePath("/app/matrix");
}

export async function dsarAction(): Promise<{ json?: string; error?: string }> {
  const user = await requireUser();
  try {
    return { json: JSON.stringify(createDsarExport(getStore(), user.id), null, 2) };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "DSAR failed" };
  }
}

export async function eraseSelfAction(): Promise<void> {
  const user = await requireUser();
  eraseUser(getStore(), user.id);
  await clearSession();
  redirect("/login");
}
