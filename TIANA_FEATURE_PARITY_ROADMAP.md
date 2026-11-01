# TIANA Django feature-parity and Cloudflare integration plan

## Scope and source of truth

- Django source: `nkem/`, `accounts/`, `core/`, `finance/`, `budgets/`, `goals/`, `insights/`, `ai_assistant/`, `notifications/`, and `marketplace/`.
- Existing PWA reference: `web/` and Cloudflare Pages Functions in `functions/`.
- Do not replace the existing Pages production branch or overwrite the separately deployed `money` Worker.
- The Django deployment is to be built and verified separately before any production domain cutover.
- The current Django source is server-backed. The original PWA is local-first and keeps financial records in the user's browser. Port useful capabilities, but do not pretend these are the same privacy model.

## Existing Django capabilities verified in source

- Welcome flow and first-run setup; registration, login, profile, theme preferences, password changes, application security and device management.
- User-owned FCFA accounts (including cash, MTN Mobile Money and Orange Money), transactions, transaction editing/deletion, and balances recalculated from the transaction ledger.
- Weekly/monthly/yearly budgets and editable weekly category allocations.
- Savings goals with image upload and a contribution flow that checks available account balance and records a ledger transfer atomically.
- Dashboard, category/weekly insights and persistent in-app notifications. Budget alerts are generated at 80% and 100%.
- Server-side Gemini money coach with per-user chat history, a limited finance snapshot, response caching and per-day usage limits.
- Staff-managed student opportunities, not a live peer-to-peer payments marketplace.
- Admin-managed brand appearance and uploaded brand assets.
- PWA app-shell caching plus offline bootstrap/synchronisation endpoints. The Django service worker deliberately does not cache authenticated HTML, API responses or media.

## Additional capabilities present in the PWA reference

These are reference implementations to evaluate and port; they are not automatically production-ready Django features.

1. **Install and offline experience**
   - Install gate with browser-specific install instructions and home-screen launch.
   - IndexedDB-backed local vault and service-worker shell caching.
   - Offline entry capture and later synchronisation in the local-first PWA. Django already has a different offline snapshot/sync mechanism; reconcile the two instead of deploying two competing workers.
2. **Backup, restore and downloads**
   - Full JSON backup export and validated JSON restore.
   - CSV export of transaction records.
   - Optional manual Google Drive backup/restore. The browser encrypts the backup with AES-256-GCM using a passphrase-derived key; this is not continuous/background sync and TIANA does not recover the passphrase.
   - Django needs account-scoped exports/imports and a safe import wizard for existing PWA JSON backups. Validate, deduplicate, preview and confirm imports; never overwrite an account silently.
3. **Firebase Cloud Messaging**
   - The PWA already has Firebase web configuration, FCM token registration/unregistration, a root-scope service worker and a Cloudflare Pages sender Function.
   - The existing PWA registers anonymous installation IDs in D1; Django must instead bind tokens to authenticated Django users and support multiple devices per user, revocation, consent and token rotation.
   - Reuse/extend the Django root-scope worker; do not register a second root-scope worker.
   - Live sending still requires the Firebase service-account JSON to be stored as an encrypted Cloudflare secret and a successful end-to-end delivery test.
4. **Privacy and analytics controls**
   - Optional analytics consent; the PWA telemetry is deliberately anonymous and does not accept financial records.
   - Django implementation must be explicit and documented. Do not silently enable analytics or send money records, prompts or profile information to analytics.
5. **Money habits and discipline**
   - Daily checklist: record spending, pause before impulse purchases, reconnect with a savings goal.
   - Calendar-based streak calculation and gentle daily progress; no shaming or manipulative streak pressure.
6. **Personalization and insights**
   - Six PWA palettes (violet, ocean, sunset, forest, rose and midnight) compared with Django's current theme choices.
   - Period-over-period spending comparison, daily/category breakdowns, savings-goal progress and a small, actionable next step.
   - Preserve Django's real Gemini coach; selectively port useful local insight rules and French/English prompt patterns without presenting deterministic rules as live AI.
7. **Campus discovery**
   - PWA sample marketplace categories, search and saved sample listings are illustrative only, unverified and not transactional.
   - Django's staff-managed opportunities are the safer persisted starting point. A genuine student-to-student marketplace needs seller identity, moderation, reporting, terms and payment/legal review before payments or escrow are introduced.
8. **Premium and monetization**
   - Django has premium entitlement fields and the AI usage-limit distinction. The PWA documentation says payments are not connected. No premium purchase, investment execution, payment collection or AdSense earnings integration is to be treated as live until provider APIs, signed webhooks, reconciliation and legal review are complete.

## Implementation backlog

### P0 — protect production and financial data
- Keep the current Pages project and existing Workers unchanged.
- Create a separate Cloudflare staging Worker/application and a separate PostgreSQL database.
- Add backup/restore procedures for database and media before migrations.
- Enforce production settings: DEBUG off, strong SECRET_KEY, explicit hosts/CSRF origins, secure cookies, HTTPS and deploy checks.
- Configure persistent object storage for uploads; local filesystem media is not durable on an ephemeral runtime.
- Validate PostgreSQL support for every migration, constraint, transaction and row-lock operation used by finance/goals.

### P1 — parity features
- [x] CSV export for transactions on the Activity screen (owner-scoped, no-store, spreadsheet-formula-safe; tests added; CI result pending).
- [ ] Add date-range and statement-summary options to CSV exports.
- JSON account export and validated import from the PWA backup format, with a pre-import preview and duplicate detection.
- Encrypted local backup and optional Google Drive app-data backup/restore; the server must never receive the passphrase or plaintext backup.
- FCM opt-in, device management, per-user token storage, push delivery, unsubscribe and dead-token cleanup.
- Unified notifications: persist in-app notifications first, then send push best-effort; do not lose financial writes when push delivery fails.
- Extend Django offline support with idempotent, owner-scoped sync and conflict handling; never cache or expose another user's data.
- Add daily money habits and streaks with user-controlled reminders and reduced-motion/accessibility support.
- Complete palette selection and saved preferences.

### P2 — experience enhancements
- Bring the welcome and onboarding artwork, transitions and mobile layouts into the Django templates.
- Make dashboard/activity/budget/goals/insights/profile screens consistent, responsive and accessible.
- Add search/filter/date-range controls and clear empty/loading/error/offline states.
- Expand insights with weekly comparison, category trends and goal ETA explanations.
- Add bilingual English/French experience where the source app already provides language patterns.
- Add account security settings, session/device revocation and privacy controls.

### P3 — later products, gated by compliance and providers
- Marketplace seller listings, trust and moderation tools.
- Payments for TIANA Premium only after a real provider integration and signed webhooks.
- Investments remain educational/coming-soon until regulated provider, jurisdiction and risk/disclosure requirements are resolved.
- Ads remain disabled until approval and valid publisher/slot configuration.

## Test gates before staging and production

- Unit/integration tests for registration, login, authorization boundaries and session security.
- Financial invariants: contribution debits the correct account once; edits/deletes recalculate balances; concurrent contributions cannot exceed goal target or account balance.
- Migration tests against PostgreSQL, not only SQLite.
- CSV/JSON export-import round trips, malformed/oversized file rejection, duplicate handling and cross-user isolation.
- Offline replay/idempotency, stale update/conflict behaviour, and proof that authenticated HTML/API/media are never cached by the service worker.
- FCM opt-in/out, multi-device registration, token rotation, invalid token cleanup and delivery to a test device.
- Gemini missing-key, invalid-key, timeout, rate-limit and daily quota tests.
- Media upload/read/delete through durable object storage and permission checks.
- `collectstatic`, `check --deploy`, smoke tests for every route, and a staging rollback rehearsal.

## Deployment prerequisites still requiring account setup

- A PostgreSQL database and connection credentials (held only as secrets); Hyperdrive configuration.
- Enable Cloudflare R2 for the account, create a bucket, and bind it to the Django Worker.
- Cloudflare Python Worker deployment configuration and a separate staging Worker name.
- Cloudflare encrypted secrets: Django SECRET_KEY, DATABASE_URL/Hyperdrive connection material as appropriate, GEMINI_API_KEY, and FIREBASE_SERVICE_ACCOUNT_JSON.
- Firebase project confirmation, Web Push/VAPID key confirmation, FCM API enabled, minimum sender role and test device.
- Google OAuth Web client ID and authorized origins for optional Drive backup.
- Custom domain only after staging checks and successful database/media restore tests.

## Non-negotiable safeguards

- Never commit `.env`, database URLs, Gemini keys, FCM service-account JSON/private keys or OAuth secrets.
- Never use D1 as the Django finance ledger without a deliberate redesign and verified transaction semantics.
- Never replace or erase the local SQLite database as part of deployment.
- Never claim FCM, payments, Drive backup, offline sync or investments are live until end-to-end tests prove them.
- Keep the existing PWA production service and Django staging environment isolated until a deliberate cutover.
