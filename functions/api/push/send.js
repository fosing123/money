import { json, sameOrigin, validDeviceId, readSmallJson, d1Available, isAdmin } from "../../_shared.js";

const TOKEN_URI = "https://oauth2.googleapis.com/token";
const FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging";
let cachedAccessToken = "";
let cachedAccessTokenExpiresAt = 0;

function base64Url(value) {
  const bytes = value instanceof Uint8Array ? value : new TextEncoder().encode(typeof value === "string" ? value : JSON.stringify(value));
  let binary = "";
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

function pemToBytes(pem) {
  const contents = String(pem || "").replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s/g, "");
  const binary = atob(contents);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function getAccessToken(account) {
  if (cachedAccessToken && Date.now() < cachedAccessTokenExpiresAt - 60000) return cachedAccessToken;
  const now = Math.floor(Date.now() / 1000);
  const unsigned = base64Url({ alg: "RS256", typ: "JWT" }) + "." + base64Url({
    iss: account.client_email,
    scope: FCM_SCOPE,
    aud: account.token_uri || TOKEN_URI,
    iat: now,
    exp: now + 3600
  });
  const key = await crypto.subtle.importKey(
    "pkcs8",
    pemToBytes(account.private_key),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(unsigned));
  const assertion = unsigned + "." + base64Url(new Uint8Array(signature));
  const response = await fetch(account.token_uri || TOKEN_URI, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion
    })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || !payload.access_token) throw new Error("Google OAuth token exchange failed (" + response.status + ").");
  cachedAccessToken = payload.access_token;
  cachedAccessTokenExpiresAt = Date.now() + Math.max(60, Number(payload.expires_in) || 3600) * 1000;
  return cachedAccessToken;
}

async function sendToFcm(projectId, accessToken, fcmToken, title, body, link, origin) {
  const response = await fetch(
    "https://fcm.googleapis.com/v1/projects/" + encodeURIComponent(projectId) + "/messages:send",
    {
      method: "POST",
      headers: { "Authorization": "Bearer " + accessToken, "Content-Type": "application/json" },
      body: JSON.stringify({
        message: {
          token: fcmToken,
          notification: { title, body },
          webpush: {
            fcm_options: { link },
            notification: { icon: origin + "/money-mark.svg", badge: origin + "/money-mark.svg" }
          }
        }
      })
    }
  );
  const result = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, result };
}

export async function onRequestPost({ request, env }) {
  if (!sameOrigin(request)) return json({ error: "Origin rejected." }, 403);
  if (!isAdmin(request, env)) return json({ error: "Admin authorization required." }, 401);
  if (!d1Available(env)) return json({ error: "D1 binding TIANA_DB is not configured." }, 503);
  if (!env.FIREBASE_SERVICE_ACCOUNT_JSON) return json({ error: "Firebase sender secret is not configured." }, 503);

  const body = await readSmallJson(request, 1600);
  if (!body.ok) return json({ error: "Invalid push message." }, body.status);
  const allowed = new Set(["title", "body", "link", "deviceId"]);
  if (Object.keys(body.value).some((key) => !allowed.has(key))) return json({ error: "Unexpected push message fields." }, 400);
  const title = typeof body.value.title === "string" ? body.value.title.trim() : "";
  const messageBody = typeof body.value.body === "string" ? body.value.body.trim() : "";
  const targetDeviceId = body.value.deviceId || "";
  if (!title || title.length > 80 || !messageBody || messageBody.length > 240) {
    return json({ error: "Title (max 80 characters) and body (max 240 characters) are required." }, 400);
  }
  if (targetDeviceId && !validDeviceId(targetDeviceId)) return json({ error: "Invalid target installation ID." }, 400);

  const origin = new URL(request.url).origin;
  let link = origin + "/";
  if (body.value.link) {
    try {
      const parsed = new URL(body.value.link, origin);
      if (parsed.origin !== origin || !["http:", "https:"].includes(parsed.protocol)) {
        return json({ error: "Notification links must stay on the TIANA website." }, 400);
      }
      link = parsed.toString();
    } catch (_) {
      return json({ error: "Invalid notification link." }, 400);
    }
  }

  let serviceAccount;
  try { serviceAccount = JSON.parse(env.FIREBASE_SERVICE_ACCOUNT_JSON); }
  catch (_) { return json({ error: "Firebase sender secret is not valid JSON." }, 503); }
  if (
    serviceAccount.type !== "service_account" ||
    serviceAccount.project_id !== "tiana-9632c" ||
    !serviceAccount.client_email ||
    !serviceAccount.private_key
  ) return json({ error: "Firebase sender secret does not match TIANA's Firebase project." }, 503);

  const query = targetDeviceId
    ? env.TIANA_DB.prepare("SELECT device_id, fcm_token FROM push_subscriptions WHERE device_id = ?1").bind(targetDeviceId)
    : env.TIANA_DB.prepare("SELECT device_id, fcm_token FROM push_subscriptions ORDER BY updated_at DESC LIMIT 200");
  const selected = await query.all();
  const subscriptions = selected.results || [];
  if (!subscriptions.length) return json({ error: targetDeviceId ? "No push subscription for that installation." : "No devices have enabled push notifications yet." }, 404);

  let accessToken;
  try { accessToken = await getAccessToken(serviceAccount); }
  catch (_) { return json({ error: "Google authentication failed. Check the rotated service-account key and FCM permission." }, 502); }

  let sent = 0, failed = 0, removed = 0;
  for (let offset = 0; offset < subscriptions.length; offset += 10) {
    const batch = subscriptions.slice(offset, offset + 10);
    const results = await Promise.all(batch.map(async (subscription) => {
      try {
        const result = await sendToFcm(serviceAccount.project_id, accessToken, subscription.fcm_token, title, messageBody, link, origin);
        if (result.ok) return "sent";
        const detail = JSON.stringify(result.result || {});
        if (result.status === 404 || detail.includes("UNREGISTERED") || detail.includes("registration-token-not-registered")) {
          await env.TIANA_DB.prepare("DELETE FROM push_subscriptions WHERE device_id = ?1").bind(subscription.device_id).run();
          return "removed";
        }
        return "failed";
      } catch (_) { return "failed"; }
    }));
    for (const result of results) {
      if (result === "sent") sent++;
      else if (result === "removed") { failed++; removed++; }
      else failed++;
    }
  }
  return json({ accepted: true, targeted: subscriptions.length, sent, failed, staleTokensRemoved: removed });
}
