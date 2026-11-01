# TIANA privacy boundary

## Local only
Manual income and expenses, balance notes, budgets, savings goals, profile name/preferences, habit log, local-rule coach messages, drafts and plaintext backups stay in localStorage/IndexedDB. The PWA app has no finance API endpoints. The service worker never caches /api/ responses.

An IndexedDB mirror helps restore the current browser snapshot if localStorage is cleared. It is not encrypted at rest, so users should lock devices and keep a tested backup.

## Operations data
Usage sharing is off by default. If enabled, TIANA receives only a random installation UUID and one of four event names: app_open (deduplicated once per day per install), pwa_installed, drive_backup, drive_restore. D1 stores the install UUID, first/last-seen, ban flag and aggregate event counts. Status checks run only for opted-in installations.

If a member turns usage sharing off, TIANA requests deletion of that installation's pseudonymous device/event rows from D1. If offline, deletion is queued locally and retried on the next connection.

No finance fields or IP addresses are written to D1. Cloudflare/network providers may still process technical metadata to run and secure the service.

## Google Drive
The browser encrypts the backup locally with AES-256-GCM before uploading directly to Google Drive app data. TIANA cannot decrypt it. This release supports explicit user-triggered backup and restore, not automatic background sync.

## Honest constraints
A device ban applies to an installation ID, not a verified human. Clearing browser data/reinstalling creates a new ID. Browser storage can be evicted; export and test backups regularly. iOS requires Safari Share -> Add to Home Screen confirmation. TIANA is a bookkeeping/financial education tool, not a bank or Mobile Money wallet.
