# Nkem

A Django-based personal finance platform for Cameroon with a mobile-first onboarding flow and dashboard.

## Quick start

1. Create a virtual environment and install requirements.
2. Copy `.env.example` to `.env` and update the variables.
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the app:
   ```bash
   python manage.py runserver
   ```
5. Visit http://localhost:8000/

## Features

- Onboarding screens
- Registration and login
- Dashboard with totals and recent activity
- Transactions, budgets, and goals
- Basic AI assistant placeholder that fails safely without credentials

## Testing

```bash
python manage.py test
```
