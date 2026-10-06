import { createDsarExport } from "../../../../lib/gdpr/dsar";
import { requireUser } from "../../../../lib/session";
import { getStore } from "../../../../lib/server-store";

export async function GET() {
  const user = await requireUser();
  const payload = createDsarExport(getStore(), user.id);
  return new Response(JSON.stringify(payload, null, 2), {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "content-disposition": 'attachment; filename="documdr-dsar.json"',
    },
  });
}
