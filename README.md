# TIANA — Your Money Friend Always

TIANA's privacy-first release is a local-first Progressive Web App for students. The production PWA is in the web/ directory and is designed for Cloudflare Pages.

## Privacy-first architecture
- Manual income, expenses, balances, budgets, savings goals and local money-coach data stay in the browser on the user's device.
- The PWA service worker caches only the app shell and static assets. It does not cache API responses.
- The optional D1 operations service stores a random installation ID, opt-in daily usage events and ban status. It has no API accepting personal finance records.
- Google Drive backup is optional. It is encrypted on the phone before the browser uploads it directly to Google's app-data area.
- Payments to TIANA and AdSense reporting are not integrated until provider APIs/webhooks are configured.

## Deploy the privacy-first PWA
Follow CLOUDFLARE_DEPLOYMENT.md. Select web as the Pages output directory. Use branch feat/tiana-pwa-offline-premium-sync-20261101 for preview testing.

The Django project at the repository root is retained as development/reference code. Do not deploy that Django finance application as the privacy-first production app: it stores finance records on a server, which conflicts with the chosen architecture.

## Local checks
The GitHub workflow checks Django history code and the privacy-first PWA JavaScript/Function files. The core manual checks are: install, offline bookkeeping, local data retention, backup/restore, usage opt-in and device ban.

The service operates offline after the first install and app-shell cache, but an internet connection is required for first download, optional usage reporting, Google Drive backup, payments and advertisements.

## Honest limits
Installation must be confirmed by the user; iOS/iPadOS users must use Safari Share -> Add to Home Screen. A device ban applies to an install ID, not a verified person. Browser storage can be cleared/evicted, so users should export and test backups.


## Firebase web integration
- The public Firebase web-app configuration is in `web/firebase-config.js`.
- `web/firebase-bootstrap.js` initializes the Firebase app using the modular Web SDK pinned to version 13.0.0.
- Firebase Analytics is loaded only after the user enables optional usage analytics in TIANA Settings. Turning that choice off disables Analytics collection.
- Firebase Cloud Messaging (push delivery) is **not enabled yet**. Add the Web Push VAPID public key, integrate FCM into the existing root-scope `web/sw.js`, and configure a server-side sender before enabling push. Do not create a second root-scope service worker.
- The Firebase web config is public client configuration, not a secret. Restrict its API key to the Firebase APIs TIANA uses and to the deployed website referrers. Never commit service-account private keys or other server credentials.
