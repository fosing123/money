import { json, isAdmin, d1Available } from "../../_shared.js";
export async function onRequestGet({ request, env }) {
  if (!isAdmin(request, env)) return json({ error: "Admin authorization required." }, 401);
  if (!d1Available(env)) return json({ error: "D1 binding TIANA_DB is not configured." }, 503);
  const db = env.TIANA_DB;
  const devices = await db.prepare(
    "SELECT COUNT(*) AS total_devices, SUM(CASE WHEN banned = 1 THEN 1 ELSE 0 END) AS banned_devices, " +
    "SUM(CASE WHEN last_seen >= datetime('now', '-1 day') THEN 1 ELSE 0 END) AS active_24h, " +
    "SUM(CASE WHEN last_seen >= datetime('now', '-7 day') THEN 1 ELSE 0 END) AS active_7d FROM devices"
  ).first();
  const usage = await db.prepare(
    "SELECT event_date, event_name, event_count FROM daily_usage WHERE event_date >= date('now', '-29 day') ORDER BY event_date DESC, event_name"
  ).all();
  const payments = await db.prepare(
    "SELECT COUNT(*) AS count, COALESCE(SUM(CASE WHEN status = 'succeeded' THEN amount_minor ELSE 0 END), 0) AS succeeded_minor FROM payment_events"
  ).first();
  return json({ devices: devices || {}, usage: usage.results || [], payments: payments || {}, paymentIntegration: "not_connected" });
}
