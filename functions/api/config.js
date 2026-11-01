import { json } from "../_shared.js";
export async function onRequestGet({ env }) {
  const googleClientId = env.GOOGLE_CLIENT_ID || "";
  const adsenseClientId = env.ADSENSE_CLIENT_ID || "";
  const adsenseSlotId = env.ADSENSE_SLOT_ID || "";
  const adsenseEnabled = /^ca-pub-\d+$/.test(adsenseClientId) && /^\d+$/.test(adsenseSlotId);
  return json({ googleClientId, adsenseClientId, adsenseSlotId, adsenseEnabled });
}
