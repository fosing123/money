import { json, validDeviceId, d1Available } from "../_shared.js";
export async function onRequestGet({ request, env }) {
  const id = new URL(request.url).searchParams.get("deviceId") || "";
  if (!validDeviceId(id)) return json({ banned: false }, 400);
  if (!d1Available(env)) return json({ banned: false, monitoringAvailable: false });
  const row = await env.TIANA_DB.prepare("SELECT banned FROM devices WHERE device_id = ?1").bind(id).first();
  return json({ banned: Boolean(row && row.banned), monitoringAvailable: true });
}
