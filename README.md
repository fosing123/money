# TIANA — Your Money Friend Always

TIANA is a Django application for student money management, built for the XAF/FCFA context. The Django project at the repository root is the application and source of truth.

## Application

- Django project: `nkem/`
- User accounts, onboarding and profiles: `accounts/`
- Accounts, income, expenses, transfers and transaction history: `finance/`
- Budget planning: `budgets/`
- Savings goals and contributions: `goals/`
- Insights: `insights/`
- Gemini money coach: `ai_assistant/`
- Notifications and Firebase device registration: `notifications/`
- Staff-managed student opportunities: `marketplace/`
- Server-rendered pages: `templates/`
- UI, PWA shell and offline queue: `static/`

## Run locally

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-django.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py check
python manage.py test
python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Use the existing Neon database locally

The basic local setup above uses SQLite by default. To use the linked Neon PostgreSQL database instead, authenticate with the Neon CLI and refresh the local environment file:

```powershell
npx neon@latest deploy
```

The Neon CLI writes `.env.local`. Django loads `.env.local` before `.env`, while existing process environment variables keep priority. For local PostgreSQL connections, Django prefers `DATABASE_URL_UNPOOLED`.

**Verify the connection before running migrations:**

```powershell
python manage.py shell -c "from django.conf import settings; d=settings.DATABASES['default']; print('ENGINE:', d['ENGINE']); print('DATABASE:', d['NAME']); print('HOST:', d['HOST'])"
```

Proceed with `python manage.py migrate` only when the engine is `django.db.backends.postgresql`, the database is `neondb`, and the host is your Neon direct endpoint (not a pooler). Never commit or share `.env.local`.

## Deploy to Cloudflare

The Django app is deployed as a Cloudflare Python Worker using `worker.py`, `pyproject.toml` and `wrangler.jsonc`. Cloudflare Workers serves the app, Hyperdrive connects it to PostgreSQL, and R2 stores user-uploaded media.

Read [CLOUDFLARE_DEPLOYMENT.md](CLOUDFLARE_DEPLOYMENT.md) before configuring the production database or deploying. The Worker is deliberately named `tiana-django-staging` while the deployment is being verified.

## Important architecture decisions

- Use PostgreSQL through Hyperdrive for financial records. Do not use D1 or Durable Objects as the finance ledger: their documented Django storage backends do not provide the transaction semantics this app needs.
- Use the `MEDIA` R2 binding for uploaded profile and goal images.
- Static assets are collected into `public/static/` and served by the Worker Assets binding.
- Local development uses SQLite and local filesystem media only.
- Never commit `.env`, service-account JSON, API keys, database credentials or customer data.
- Do not run migrations against a production database until a backup and a reviewed data-import plan exist.

## Feature boundaries

The marketplace currently provides staff-managed opportunities; it is not a payment gateway or escrow service. Premium and investments are not represented as paid financial services until real provider integrations and compliance checks exist.
