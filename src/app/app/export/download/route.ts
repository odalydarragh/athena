import { exportTechnicalFile } from "../../../../lib/compile/technical-file";
import { requireUser } from "../../../../lib/session";
import { getStore } from "../../../../lib/server-store";

export async function GET() {
  const user = await requireUser();
  try {
    const file = exportTechnicalFile(getStore(), user.organizationId);
    return new Response(JSON.stringify(file, null, 2), {
      headers: {
        "content-type": "application/json; charset=utf-8",
        "content-disposition": 'attachment; filename="documdr-technical-file.json"',
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "export blocked";
    return new Response(message, { status: 403 });
  }
}
