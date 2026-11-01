# TIANA Django on Cloudflare Workers

This repository deploys the Django application in `nkem/` to a **separate staging Worker** named `tiana-django-staging`. It does not change the existing `tiana-money` Pages production site or the existing `money` Worker.

## Architecture

- **Application runtime:** Cloudflare Python Workers with Django's WSGI adapter.
- **Financial database:** PostgreSQL through Cloudflare Hyperdrive.
- **Uploaded profile and goal images:** Cloudflare R2, using the `MEDIA` bucket binding and Cloudflare's `django-cf` R2 storage backend.
- **Static files:** `collectstatic` writes to `public/static/`; the Worker Assets binding serves `/static/*`.
- **Local development:** SQLite and local filesystem uploads. Those local defaults are not permitted in production.

Do not use D1 or the Django Durable Object SQLite backend as the financial ledger. Cloudflare documents that these Django database backends do not support database transactions; TIANA's ledger and goal-contribution flows rely on transactional behaviour.

## Required Cloudflare setup

### 1. PostgreSQL and Hyperdrive

Create or choose a PostgreSQL database with a provider such as Neon or Supabase. Create a Cloudflare Hyperdrive configuration pointing to that database. Keep its connection credentials private.

Then edit the commented `hyperdrive` block in `wrangler.jsonc` and add the real Hyperdrive configuration ID:

```jsonc
"hyperdrive": [
  {
    "binding": "HYPERDRIVE",
    "id": "YOUR_REAL_HYPERDRIVE_CONFIG_ID"
  }
]
```

Do not use the old D1 database for the Django ledger. Do not run migrations or import local SQLite data into a live database until a backup and reviewed import plan exist.

### 2. R2 for uploaded media

The Cloudflare R2 bucket `tiana-django-media` has already been created. Keep the `MEDIA` binding in `wrangler.jsonc`; the Django storage adapter writes media under the `tiana-media/` prefix.

No S3 access keys are needed by the application when it uses the Worker R2 binding. Before the first staging upload test, verify the deployed Worker has the `MEDIA` binding attached to this bucket.

### 3. Worker configuration and secrets

Configure these Worker variables/secrets in Cloudflare:

| Name | Type | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | Secret | Long, random Django signing key |
| `ALLOWED_HOSTS` | Variable | Comma-separated staging hostnames |
| `CSRF_TRUSTED_ORIGINS` | Variable | Full HTTPS origin(s), comma-separated |
| `GEMINI_API_KEY` | Secret | Server-side Gemini API key |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Secret | Firebase service-account JSON for server-side FCM |
| `FIREBASE_WEB_API_KEY` | Variable | Public Firebase Web app config |
| `FIREBASE_WEB_AUTH_DOMAIN` | Variable | Public Firebase Web app config |
| `FIREBASE_WEB_PROJECT_ID` | Variable | Public Firebase Web app config |
| `FIREBASE_WEB_MESSAGING_SENDER_ID` | Variable | Public Firebase Web app config |
| `FIREBASE_WEB_APP_ID` | Variable | Public Firebase Web app config |
| `FIREBASE_WEB_VAPID_KEY` | Variable | Public Web Push key |

Never put any private value into Git, `wrangler.jsonc`, client-side JavaScript or a committed `.env` file.

### 4. Local verification

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node.js, then run:

```powershell
uv sync --all-groups
Copy-Item .env.example .env
uv run python manage.py migrate
uv run python manage.py check
uv run python manage.py test
uv run python manage.py collectstatic --noinput
uv run pywrangler dev
```

The local Worker can serve the Django app shell, but database-backed pages need a configured local PostgreSQL/Hyperdrive development connection. Do not mistake a local SQLite run for a production readiness test.

### 5. First staging deployment

Before deploying, confirm:
- The Hyperdrive ID is configured and the PostgreSQL database is reachable.
- R2 has been enabled and the `tiana-django-media` bucket exists.
- Worker secrets and hostname/CSRF variables are configured.
- The Django CI workflow passes.
- A backup exists before any live data import.

The repository includes `.github/workflows/deploy-worker.yml` for a staging Worker deployment. Add GitHub Actions secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` to the `tiana-django-staging` environment. The API token must have permission to deploy Workers. The workflow is configured for manual staging deployment and future pushes to `main`; it does not switch the Pages production site.

## Current cutover policy

The existing Pages project `tiana-money` still serves the previous static prototype from its production branch. Keep it in place until the Django Worker passes authentication, financial ledger, backup/restore, uploads, notifications, and load checks. Only then should the production hostname or DNS be moved to the Django Worker.
