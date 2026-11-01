export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "private, no-store, max-age=0",
      "X-Content-Type-Options": "nosniff"
    }
  });
}
export function sameOrigin(request) {
  const origin = request.headers.get("Origin");
  if (!origin) return true;
  try { return new URL(origin).origin === new URL(request.url).origin; }
  catch (_) { return false; }
}
export function validDeviceId(value) {
  return typeof value === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}
function constantTimeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}
export function isAdmin(request, env) {
  const expected = env.ADMIN_TOKEN || "";
  const supplied = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  return Boolean(expected && supplied && constantTimeEqual(supplied, expected));
}
export async function readSmallJson(request, maxBytes = 1200) {
  const declared = Number(request.headers.get("Content-Length") || 0);
  if (declared > maxBytes) return { ok: false, status: 413 };
  const raw = await request.text();
  if (new TextEncoder().encode(raw).length > maxBytes) return { ok: false, status: 413 };
  try {
    const value = JSON.parse(raw);
    return value && typeof value === "object" && !Array.isArray(value) ? { ok: true, value } : { ok: false, status: 400 };
  } catch (_) { return { ok: false, status: 400 }; }
}
export function d1Available(env) {
  return Boolean(env && env.TIANA_DB && typeof env.TIANA_DB.prepare === "function");
}
