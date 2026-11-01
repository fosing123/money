CREATE TABLE IF NOT EXISTS devices (
 device_id TEXT PRIMARY KEY, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
 banned INTEGER NOT NULL DEFAULT 0 CHECK (banned IN (0,1)), ban_reason TEXT, banned_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen);
CREATE INDEX IF NOT EXISTS idx_devices_banned ON devices(banned);
CREATE TABLE IF NOT EXISTS device_event_days (
 device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
 event_date TEXT NOT NULL,
 event_name TEXT NOT NULL CHECK (event_name IN ('app_open','pwa_installed','drive_backup','drive_restore')),
 PRIMARY KEY(device_id,event_date,event_name)
);
CREATE TABLE IF NOT EXISTS daily_usage (
 event_date TEXT NOT NULL,event_name TEXT NOT NULL,event_count INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(event_date,event_name)
);
-- Reserved only for verified fees paid to TIANA, never personal finance entries.
CREATE TABLE IF NOT EXISTS payment_events (
 id TEXT PRIMARY KEY,provider TEXT NOT NULL,provider_reference TEXT NOT NULL UNIQUE,
 amount_minor INTEGER NOT NULL CHECK(amount_minor>=0),currency TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('pending','succeeded','failed','refunded')),
 created_at TEXT NOT NULL,verified_at TEXT
);
