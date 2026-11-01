import { json, sameOrigin, validDeviceId, readSmallJson, d1Available } from "../_shared.js";
const ALLOWED_EVENTS = new Set(["app_open", "pwa_installed", "drive_backup", "drive_restore"]);
export async function onRequestPost({ request, env }) {
  if (!sameOrigin(request)) return json({ error: "Origin rejected." }, 403);
  if (!d1Available(env)) return json({ error: "Usage monitoring is unavailable." }, 503);
  const body = await readSmallJson(request, 1000);
  if (!body.ok) return json({ error: "Invalid telemetry request." }, body.status);
  const keys = Object.keys(body.value).sort();
  if (keys.length !== 2 || keys[0] !== "deviceId" || keys[1] !== "event") {
    return json({ error: "Only a device ID and whitelisted event are accepted." }, 400);
  }
  const { deviceId, event } = body.value;
  if (!validDeviceId(deviceId) || !ALLOWED_EVENTS.has(event)) return json({ error: "Invalid usage event." }, 400);
  const db = env.TIANA_DB, now = new Date().toISOString(), day = now.slice(0, 10);
  const banned = await db.prepare("SELECT banned FROM devices WHERE device_id = ?1").bind(deviceId).first();
  if (banned && banned.banned) return json({ error: "This installation is blocked." }, 403);
  await db.prepare(
    "INSERT INTO devices (device_id, first_seen, last_seen, banned) VALUES (?1, ?2, ?2, 0) " +
    "ON CONFLICT(device_id) DO UPDATE SET last_seen = excluded.last_seen"
  ).bind(deviceId, now).run();
  const inserted = await db.prepare(
    "INSERT OR IGNORE INTO device_event_days (device_id, event_date, event_name) VALUES (?1, ?2, ?3)"
  ).bind(deviceId, day, event).run();
  if (inserted.meta && inserted.meta.changes) {
    await db.prepare(
      "INSERT INTO daily_usage (event_date, event_name, event_count) VALUES (?1, ?2, 1) " +
      "ON CONFLICT(event_date, event_name) DO UPDATE SET event_count = event_count + 1"
    ).bind(day, event).run();
  }
  return json({ accepted: true });
}
