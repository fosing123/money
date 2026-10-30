# Nkem Django application

## Local setup

    python -m venv .venv
    # Windows: .venv\Scripts\Activate.ps1
    # Linux/macOS: source .venv/bin/activate
    pip install -r requirements-django.txt
    # Copy .env.example to .env (PowerShell: Copy-Item .env.example .env)
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py check
    python manage.py test
    python manage.py runserver

Open http://127.0.0.1:8000/ and the admin at http://127.0.0.1:8000/admin/.

## Features

- Five-screen welcome flow plus a four-step first-run setup.
- Registration/login, profile, preference/theme setting and logout via POST.
- FCFA accounts for cash, MTN Mobile Money, Orange Money and bank accounts.
- Transactions with owner-scoped account choices, validation, filtering, edit/delete, and ledger-derived balances.
- Weekly/monthly/yearly category budgets, savings goals with optional images and target dates, category/weekly insights and notifications.
- Staff-managed student opportunity listings with search and detail pages.
- TIANA money coach calling Gemini from the server only; chats are saved per member, and provider errors are handled without exposing credentials.
- Django admin for app appearance, brand/onboarding/dashboard/coach images, users, accounts, transactions, goals, budgets, notifications, opportunities and AI conversations.

## Environment variables

- DEBUG=0 for production.
- SECRET_KEY must be a long random private value on the server.
- ALLOWED_HOSTS is a comma-separated list of site hostnames.
- CSRF_TRUSTED_ORIGINS is a comma-separated list of full origins, including https://.
- DATABASE_URL accepts sqlite:///db.sqlite3 locally or a PostgreSQL URL in production.
- GEMINI_API_KEY is the production Gemini API key. Keep it in the server environment or an untracked .env, never in browser JavaScript, templates or Git.
- AI_PROVIDER=gemini and GEMINI_MODEL=gemini-3.8-flash select the provider/model; set AI_PROVIDER=none to disable it.
- SECURE_SSL_REDIRECT=1 when HTTPS is configured at the reverse proxy/load balancer.
- Configure SMTP variables if email delivery is enabled.

## Production checklist

1. Back up the database and media before deploying.
2. Set DEBUG=0, SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, database URL, Gemini key and SMTP values on the server.
3. Install requirements, run migrations, then python manage.py check --deploy.
4. Run python manage.py collectstatic --noinput; serve /static/ through WhiteNoise or the configured web server, and serve uploaded /media/ files through durable storage or a protected web-server mapping.
5. Use Gunicorn or another production WSGI/ASGI server behind HTTPS, with process supervision and log rotation; never expose runserver.
6. Test registration, onboarding, account creation, transaction add/edit/delete, budgets, goal upload, opportunity listing, admin image upload and Gemini API errors.
7. Ensure backups cover both the database and MEDIA_ROOT; test an actual restore.

## Boundaries

The student marketplace is a staff-managed opportunity catalogue, not an escrow/payment gateway. The pages do not process transfers, deposits or payouts. The Gemini coach provides educational guidance, not licensed financial advice. The static prototype remains a reference and is not the production server entry point.