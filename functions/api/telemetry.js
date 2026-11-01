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
  // Keep the operational database bounded: retain per-install event dedupe rows
  // and aggregate daily counters for 90 days; purge dormant install IDs after a year.
  await db.prepare("DELETE FROM device_event_days WHERE event_date < date('now', '-90 day')").run();
  await db.prepare("DELETE FROM daily_usage WHERE event_date < date('now', '-90 day')").run();
  await db.prepare("DELETE FROM devices WHERE julianday(last_seen) < julianday('now', '-365 day')").run();
  return json({ accepted: true });
}


export async function onRequestDelete({ request, env }) {
  if (!sameOrigin(request)) return json({ error: "Origin rejected." }, 403);
  if (!d1Available(env)) return json({ error: "Usage deletion is temporarily unavailable." }, 503);
  const id = new URL(request.url).searchParams.get("deviceId") || "";
  if (!validDeviceId(id)) return json({ error: "Invalid installation ID." }, 400);
  const db = env.TIANA_DB;
  const events = await db.prepare("SELECT event_date, event_name FROM device_event_days WHERE device_id = ?1").bind(id).all();
  for (const item of (events.results || [])) {
    await db.prepare("UPDATE daily_usage SET event_count = CASE WHEN event_count > 0 THEN event_count - 1 ELSE 0 END WHERE event_date = ?1 AND event_name = ?2").bind(item.event_date, item.event_name).run();
  }
  await db.prepare("DELETE FROM daily_usage WHERE event_count <= 0").run();
  await db.prepare("DELETE FROM devices WHERE device_id = ?1").bind(id).run();
  return json({ deleted: true });
}
