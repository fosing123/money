# TIANA Cloudflare Pages deployment

1. Create a Cloudflare account, add your existing domain and create a Pages project connected to this GitHub repository.
2. Deploy branch feat/tiana-pwa-offline-premium-sync-20261101 for preview. Use no build command and set the output directory to web.
3. Add the custom domain and follow Cloudflare DNS/HTTPS instructions. HTTPS is required for PWA installation, IndexedDB and browser encryption.
4. Create D1 database tiana-ops and apply migrations/0001_telemetry.sql.
5. Bind that database to the Pages project with the binding name exactly TIANA_DB.
6. Add secret ADMIN_TOKEN (generate a long random value). Add public variable GOOGLE_CLIENT_ID after configuring Google OAuth.
7. Optionally add public ADSENSE_CLIENT_ID and ADSENSE_SLOT_ID only after AdSense approves the site.

Pages Functions in functions/ are discovered automatically. D1 must be bound under TIANA_DB.

## Google Drive setup
Enable Google Drive API in Google Cloud Console. Configure the OAuth consent screen and create a Web application OAuth client. Add the production domain as an authorized JavaScript origin. Set the OAuth client ID in Pages variables as GOOGLE_CLIENT_ID.

Member-triggered backups are encrypted on-device with AES-256-GCM and a passphrase-derived key before the browser uploads ciphertext directly to Google's app-data area. TIANA's server never receives the backup, passphrase or Google access token. This version is manual backup/restore, not continuous background sync. Keep the passphrase safe; TIANA cannot recover it.

For Apple devices, export a local backup JSON and save it to iCloud Drive via Files/share sheet. A browser PWA does not have a general-purpose iCloud Drive sync API.

## Privacy
The Functions accept only an anonymous installation UUID and whitelisted usage-event names. They have no route that receives balance, income, expenses, transactions, budgets, goals, profile fields or money-coach messages. D1 stores install IDs, first/last-seen, bans and daily aggregate events. Cloudflare may process network metadata to provide the service, but TIANA's D1 tables do not store IP addresses.

Usage reporting is off by default. Opting out requests deletion of that install's D1 telemetry rows; an offline deletion is queued and retried later. A ban is a deterrent only: clearing browser data or reinstalling creates a new ID because this PWA collects no user identity.

## Payments and ads
D1 has a reserved table for verified payments to TIANA only. No gateway webhook is connected yet. A real provider's signed server-to-server webhook must be implemented before treating a payment as confirmed. Do not accept client-reported payment confirmations.

Money School has an optional AdSense slot. Configure publisher/ad-slot IDs only after Google approves the site. The AdSense reporting API is not connected; use your AdSense dashboard for impressions, RPM and earnings until that integration is added.

## Admin
Open /admin.html on the deployed domain and enter the Cloudflare ADMIN_TOKEN. It is held in the tab's memory only. The console shows opt-in anonymous installs, aggregate events and ban/unban controls. It does not show members' financial data.

## Test checklist
- Normal browser visit shows the install gate.
- Install TIANA and open it via the home-screen icon.
- Complete onboarding; first balance is zero unless the user enters another value.
- Turn off Wi-Fi/data and try adding income, expenses, budgets and goals.
- Reconnect and confirm entries remain local.
- Export JSON, restore on a second device, then test encrypted Drive backup/restore.
- Opt into usage reporting; confirm the installation appears in admin; ban and unban it.
- Inspect DevTools Network and confirm no finance data is sent.

The GitHub branch does not configure your Cloudflare domain, D1 binding, secrets or Google OAuth client. Those setup steps must be completed in your accounts.


## Firebase Cloud Messaging setup
1. Confirm Firebase Cloud Messaging is enabled and the Web Push public key shown in `web/firebase-config.js` matches the project's current VAPID public key.
2. Enable the Firebase Cloud Messaging API in the linked Google Cloud project.
3. Revoke the service-account key shared in the setup conversation and generate a replacement key for the same service account. Grant the service account only the Firebase Cloud Messaging Service Editor role (`roles/cloudmessaging.editor`) if your project permits it.
4. In Cloudflare Dashboard, open Workers & Pages > your Pages project > Settings > Variables and Secrets. Add `FIREBASE_SERVICE_ACCOUNT_JSON` as an **encrypted Secret**, and paste the complete replacement service-account JSON. Configure it for Preview and Production as needed. Never add it to GitHub, `wrangler.jsonc`, frontend code or a plain-text variable.
5. Apply the push migration to the D1 database already bound as `TIANA_DB`: `npx wrangler d1 execute tiana-ops --remote --file=migrations/0002_push.sql`.
6. Redeploy the Pages project so the Functions and secret are active.
7. Open the installed TIANA PWA, go to Settings and enable notifications. Confirm an installation appears in the admin list.
8. Open `/admin.html`, connect with `ADMIN_TOKEN`, choose the target installation with “Use for push”, and send a test notification.
9. Verify background delivery, that clicking the notification opens TIANA, and that disabling push removes the server-side token.

The Pages Functions use FCM HTTP v1 and Web Crypto to create a short-lived OAuth assertion from `FIREBASE_SERVICE_ACCOUNT_JSON`. The Python Firebase Admin SDK snippet does not run inside Cloudflare Pages Functions. The service-account private key remains server-side.
