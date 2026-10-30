# TIANA — Your money friend

TIANA is a mobile-first personal money companion designed around students and young adults in Cameroon. This repository preserves the original static prototype as a product/design reference and adds a Django application with user-owned records, authentication, budgeting, goals, a server-side AI coach, student opportunities and admin-managed branding/media.

## Current Django application

The Django application lives at the repository root: manage.py, nkem/, and the domain apps. Follow DJANGO_README.md for local and production setup.

- Member experience: five-screen introduction, registration/login, guided first-run setup, dashboard, transaction history, budgets, goals, insights, notifications, student opportunities, profile and AI chat.
- Money records: account opening balances are tracked separately from transactions; balances recalculate when ledger entries are created, edited or deleted.
- Visuals: responsive purple-first interface, alternative palettes, onboarding artwork, optional goal/opportunity image uploads and staff-managed brand image slots.
- AI: Gemini is called from the Django server with a limited per-user financial summary and a safe fallback when the provider is not configured.
- Admin: app appearance, brand/onboarding/dashboard/coach images, users, accounts, transactions, goals, budgets, notifications, opportunities and saved AI conversations.

## Development and deployment

1. Install dependencies from requirements-django.txt.
2. Copy .env.example to .env and keep real keys and passwords out of Git.
3. Run python manage.py migrate, create a staff account with python manage.py createsuperuser, then run python manage.py runserver.
4. Read the production checklist in DJANGO_README.md before exposing the site.

The original index.html / app.js prototype is kept as a design reference. GitHub Pages alone cannot run Django; production must run Django through a production WSGI/ASGI server.