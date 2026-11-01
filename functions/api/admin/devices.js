import { json, isAdmin, d1Available } from "../../_shared.js";
export async function onRequestGet({ request, env }) {
  if (!isAdmin(request, env)) return json({ error: "Admin authorization required." }, 401);
  if (!d1Available(env)) return json({ error: "D1 binding TIANA_DB is not configured." }, 503);
  const result = await env.TIANA_DB.prepare(
    "SELECT device_id, first_seen, last_seen, banned, ban_reason, banned_at FROM devices ORDER BY last_seen DESC LIMIT 200"
  ).all();
  return json({ devices: result.results || [] });
}
