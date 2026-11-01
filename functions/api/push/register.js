import { json, sameOrigin, validDeviceId, readSmallJson, d1Available } from "../../_shared.js";

export async function onRequestPost({ request, env }) {
  if (!sameOrigin(request)) return json({ error: "Origin rejected." }, 403);
  if (!d1Available(env)) return json({ error: "Push registration is unavailable." }, 503);
  const body = await readSmallJson(request, 6000);
  if (!body.ok) return json({ error: "Invalid push registration." }, body.status);
  const keys = Object.keys(body.value).sort();
  if (keys.length !== 2 || keys[0] !== "deviceId" || keys[1] !== "token") {
    return json({ error: "Only an installation ID and FCM token are accepted." }, 400);
  }
  const { deviceId, token } = body.value;
  if (!validDeviceId(deviceId) || typeof token !== "string" || token.length < 40 || token.length > 5000) {
    return json({ error: "Invalid installation ID or FCM token." }, 400);
  }

  const db = env.TIANA_DB;
  const existing = await db.prepare("SELECT banned FROM devices WHERE device_id = ?1").bind(deviceId).first();
  if (existing && existing.banned) return json({ error: "This installation is blocked." }, 403);
  const now = new Date().toISOString();
  await db.prepare(
    "INSERT INTO devices (device_id, first_seen, last_seen, banned) VALUES (?1, ?2, ?2, 0) " +
    "ON CONFLICT(device_id) DO UPDATE SET last_seen = excluded.last_seen"
  ).bind(deviceId, now).run();
  await db.prepare(
    "INSERT INTO push_subscriptions (device_id, fcm_token, created_at, updated_at) VALUES (?1, ?2, ?3, ?3) " +
    "ON CONFLICT(device_id) DO UPDATE SET fcm_token = excluded.fcm_token, updated_at = excluded.updated_at"
  ).bind(deviceId, token, now).run();
  return json({ registered: true });
}

export async function onRequestDelete({ request, env }) {
  if (!sameOrigin(request)) return json({ error: "Origin rejected." }, 403);
  if (!d1Available(env)) return json({ error: "Push registration is unavailable." }, 503);
  const id = new URL(request.url).searchParams.get("deviceId") || "";
  if (!validDeviceId(id)) return json({ error: "Invalid installation ID." }, 400);
  await env.TIANA_DB.prepare("DELETE FROM push_subscriptions WHERE device_id = ?1").bind(id).run();
  return json({ removed: true });
}
