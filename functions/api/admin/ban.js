import { json, isAdmin, sameOrigin, validDeviceId, readSmallJson, d1Available } from "../../_shared.js";
export async function onRequestPost({ request, env }) {
  if (!isAdmin(request, env)) return json({ error: "Admin authorization required." }, 401);
  if (!sameOrigin(request)) return json({ error: "Origin rejected." }, 403);
  if (!d1Available(env)) return json({ error: "D1 binding TIANA_DB is not configured." }, 503);
  const parsed = await readSmallJson(request, 900);
  if (!parsed.ok) return json({ error: "Invalid admin request." }, parsed.status);
  const { deviceId, banned, reason = "" } = parsed.value;
  if (!validDeviceId(deviceId) || typeof banned !== "boolean" || typeof reason !== "string" || reason.length > 240) {
    return json({ error: "Invalid device moderation values." }, 400);
  }
  const now = new Date().toISOString();
  const row = await env.TIANA_DB.prepare("SELECT device_id FROM devices WHERE device_id = ?1").bind(deviceId).first();
  if (!row) return json({ error: "Unknown installation ID. It must first opt in to anonymous usage reporting." }, 404);
  await env.TIANA_DB.prepare(
    "UPDATE devices SET banned = ?1, ban_reason = ?2, banned_at = ?3 WHERE device_id = ?4"
  ).bind(banned ? 1 : 0, banned ? reason.trim() : null, banned ? now : null, deviceId).run();
  return json({ updated: true, banned });
}
