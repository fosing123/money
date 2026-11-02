"""Cloudflare Python Worker entry point for the TIANA Django app.

Initialize Django once during isolate startup, following Cloudflare's
Python Workers WSGI integration pattern. Static assets are served from the
Worker Assets binding and uploaded media from the dedicated R2 bucket.
"""
import os
import traceback
from urllib.parse import unquote, urlsplit

from workers import Response, WorkerEntrypoint, env, wsgi


def _copy_secret(source_env, source, target=None):
    value = getattr(source_env, source, None)
    if value is not None and str(value):
        os.environ[target or source] = str(value)


# Read environment variables and secrets from the Worker global env binding
# before importing Django settings or starting the application registry.
for source, target in {
    "DJANGO_SECRET_KEY": "SECRET_KEY",
    "ALLOWED_HOSTS": "ALLOWED_HOSTS",
    "CSRF_TRUSTED_ORIGINS": "CSRF_TRUSTED_ORIGINS",
    "GEMINI_API_KEY": "GEMINI_API_KEY",
    "FIREBASE_SERVICE_ACCOUNT_JSON": "FIREBASE_SERVICE_ACCOUNT_JSON",
    "FIREBASE_WEB_API_KEY": "FIREBASE_WEB_API_KEY",
    "FIREBASE_WEB_AUTH_DOMAIN": "FIREBASE_WEB_AUTH_DOMAIN",
    "FIREBASE_WEB_PROJECT_ID": "FIREBASE_WEB_PROJECT_ID",
    "FIREBASE_WEB_MESSAGING_SENDER_ID": "FIREBASE_WEB_MESSAGING_SENDER_ID",
    "FIREBASE_WEB_APP_ID": "FIREBASE_WEB_APP_ID",
    "FIREBASE_WEB_VAPID_KEY": "FIREBASE_WEB_VAPID_KEY",
}.items():
    _copy_secret(env, source, target)

os.environ["DEBUG"] = "0"
os.environ["DB_CONN_MAX_AGE"] = "0"
os.environ["DJANGO_DB_BACKEND"] = "nkem.db_backends.pg8000"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nkem.settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

_hyperdrive = getattr(env, "HYPERDRIVE", None)
_connection_string = getattr(_hyperdrive, "connectionString", None) if _hyperdrive else None
if _connection_string:
    os.environ["DATABASE_URL"] = str(_connection_string)

_application = None
_startup_error = None

if not _connection_string:
    _startup_error = "Cloudflare Hyperdrive binding HYPERDRIVE is missing or has no connection string."
elif not os.environ.get("SECRET_KEY") or not os.environ.get("ALLOWED_HOSTS"):
    _startup_error = "Required Django settings are missing: SECRET_KEY and/or ALLOWED_HOSTS."
else:
    try:
        from django.core.wsgi import get_wsgi_application

        _application = get_wsgi_application()
        print("TIANA Django WSGI application initialized successfully.")
    except Exception:
        _startup_error = traceback.format_exc()
        print("TIANA Django startup failed:")
        print(_startup_error)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlsplit(request.url).path

        # Public static assets are served directly from the bundled asset store.
        if path.startswith("/static/"):
            return await self.env.ASSETS.fetch(request)

        # Django's R2Storage returns /media/<key> URLs. Keep user uploads off disk.
        if path.startswith("/media/"):
            key = unquote(path[len("/media/"):]).lstrip("/")
            item = await self.env.MEDIA.get(key)
            if item is None:
                return Response("Not found", status=404)
            metadata = getattr(item, "httpMetadata", None)
            content_type = getattr(metadata, "contentType", None) or "application/octet-stream"
            return Response(item.body, headers={
                "Content-Type": content_type,
                "Cache-Control": "private, max-age=60",
                "X-Content-Type-Options": "nosniff",
            })

        # Do not retry Django setup after a failed startup. Django's app registry
        # is not re-entrant; a retry would hide the original startup exception.
        if _application is None:
            print("TIANA request rejected because Django did not initialize.")
            return Response(
                "TIANA is temporarily unavailable because the Django application failed to start. Check Worker Logs.",
                status=503,
            )

        return await wsgi.fetch(_application, request, self.env)
