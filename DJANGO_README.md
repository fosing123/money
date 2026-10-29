# TIANA — Django money companion

TIANA is the server-backed version of the earlier static money-management prototype. The static app is a visual/product reference; this Django project owns accounts, transactions, budgets, goals, onboarding preferences, and server-side AI requests.

## What is in this branch

- A mobile-first, responsive TIANA design system, rebuilt onboarding, balance overview, transaction history, budgets, savings goals, profile theme palettes, and a student-opportunity catalogue.
- A guided first-run setup that stores weekly income and savings targets, payday, financial priorities, and the opening balance of the chosen Cash / MTN Mobile Money / Orange Money / bank account.
- Transaction-ledger balance recalculation on create, update, and delete; account choices are scoped to the signed-in user.
- Admin-managed global brand colours and image slots for the logo, five onboarding screens, dashboard hero, AI coach, marketplace, profile, and empty states. Staff can also upload per-goal and per-opportunity images.
- Gemini REST integration on the server. No API key is shipped to browser JavaScript. If no key is configured, the interface says so instead of pretending the AI answered live.
- Upload checks for common image formats and a 5 MB maximum. Use HTTPS and ensure uploaded media is never executed by the web server.

## Local setup

Python 3.13 is recommended for the included CI workflow. From the repository root:

\`\`\`powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements-django.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
\`\`\`

Open \`http://127.0.0.1:8000/\`. \`runserver\` is for development only.

## Brand and image management

1. Sign in to \`/admin/\` with a staff/superuser account.
2. In **Core → App appearance**, set the site name, tagline, and six-digit hex colours. Only one appearance configuration is allowed.
3. In **Core → Brand images**, upload an image for the relevant slot. Upload JPG, PNG or WebP images smaller than 5 MB. Keep one active image per slot.
4. Goal and opportunity images can be set on their individual admin records.

Uploaded media lives in \`MEDIA_ROOT\` (default: \`media/\`). Back it up with the database. In production, serve media from a non-executable storage location or object store; do not run uploaded files as code.

## Gemini AI coach

The coach reads a small summary of the signed-in user's own month-to-date totals, budgets, goals and recent transaction categories. It deliberately does not send passwords, full account identifiers, merchant names, or other profile identifiers.

Set these in the *server environment* (or a local untracked \`.env\`):

\`\`\`dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=your-real-key
GEMINI_MODEL=gemini-2.5-flash
\`\`\`

The real key is not a source-code value. Do not paste it in GitHub, the browser, templates, JavaScript, screenshots, or chat history. The code uses the Gemini REST \`generateContent\` endpoint with the \`x-goog-api-key\` request header. AI errors are reduced to user-safe messages; the app never displays upstream diagnostics.

## Database and production notes

- Local runs use SQLite by default. For a multi-user production deployment, configure \`DATABASE_URL\` to PostgreSQL and keep that URL private.
- Set \`DEBUG=0\`, a strong unique \`SECRET_KEY\`, accurate \`ALLOWED_HOSTS\`, HTTPS \`CSRF_TRUSTED_ORIGINS\`, and appropriate email settings.
- Install dependencies, run \`python manage.py migrate\`, \`python manage.py collectstatic --noinput\`, and create a superuser.
- Use Gunicorn/ASGI plus a reverse proxy, not \`manage.py runserver\`. Configure the reverse proxy to serve \`STATIC_ROOT\` and \`MEDIA_ROOT\` appropriately; never execute media uploads.
- Run \`python manage.py check --deploy\` against production settings before opening the app to the public.
- Back up both the database and uploaded media. Test restore procedures before deployment.

## Checks

\`\`\`bash
python manage.py check
python manage.py migrate --noinput
python manage.py test --verbosity=2
\`\`\`

The GitHub Actions workflow runs the same system checks and tests. Real Gemini behavior still requires a server-side API key, so CI leaves the key blank and tests the disclosed preview mode.