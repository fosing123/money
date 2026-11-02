"""Cloudflare Python Worker entry point for the TIANA Django app.

Django initialization is synchronous and happens once per isolate before the
first WSGI dispatch. The WSGI adapter manages requests; do not serialize the
entire request lifecycle behind a global asyncio lock.
"""
import json
import os
import traceback
from urllib.parse import unquote, urlsplit

from workers import Response, WorkerEntrypoint, env, wsgi

_application = None
_initialization_attempted = False
_startup_error = None


def _copy_secret(source_env, source, target=None):
    value = getattr(source_env, source, None)
    if value is not None and str(value):
        os.environ[target or source] = str(value)


def _initialize_django(source_env):
    """Initialize Django once, after reading the Worker environment bindings."""
    global _application, _initialization_attempted, _startup_error

    if _initialization_attempted:
        return

    # Python code runs synchronously within one isolate. Do all initialization
    # before the first await so concurrent fetches cannot observe a half-built app.
    _initialization_attempted = True

    try:
        required = {
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
        }
        for source, target in required.items():
            _copy_secret(source_env, source, target)

        hyperdrive = getattr(source_env, "HYPERDRIVE", None)
        connection_string = (
            getattr(hyperdrive, "connectionString", None) if hyperdrive else None
        )
        if not connection_string:
            raise RuntimeError(
                "Cloudflare Hyperdrive binding HYPERDRIVE is missing or has no connection string."
            )

        os.environ["DATABASE_URL"] = str(connection_string)
        os.environ["DEBUG"] = "0"
        os.environ["CLOUDFLARE_WORKER"] = "1"
        os.environ["DB_CONN_MAX_AGE"] = "0"
        os.environ["DJANGO_DB_BACKEND"] = "nkem.db_backends.pg8000"
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nkem.settings")
        os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

        if not os.environ.get("SECRET_KEY") or not os.environ.get("ALLOWED_HOSTS"):
            raise RuntimeError(
                "Required Django settings are missing: SECRET_KEY and/or ALLOWED_HOSTS."
            )

        # Import the Django WSGI app at module initialization so Cloudflare can
        # include it in the Python Worker memory snapshot. This moves Django's
        # costly app loading out of user-facing cold requests.
        from django.core.wsgi import get_wsgi_application

        _application = get_wsgi_application()
        print("TIANA Django WSGI application initialized successfully.")
    except Exception:
        _startup_error = traceback.format_exc()
        print("TIANA Django startup failed:")
        print(_startup_error)



# Worker bindings are available in module scope. Initialize Django here so the
# WSGI application is included in Cloudflare's deployment-time memory snapshot.
_initialize_django(env)
if _application is None:
    raise RuntimeError(
        "TIANA Django could not initialize during Worker startup; check Worker logs."
    )


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlsplit(request.url).path

        # Public static assets are served directly from the bundled asset store.
        if path.startswith("/static/"):
            return await self.env.ASSETS.fetch(request)

        # Keep root-level public files out of Django's Python startup path.
        if path in {"/service-worker.js", "/robots.txt", "/favicon.ico"}:
            return await self.env.ASSETS.fetch(request)

        # Public Firebase Web configuration does not require Django startup.
        if path == "/firebase-config.js":
            config = {
                "apiKey": getattr(self.env, "FIREBASE_WEB_API_KEY", "") or "",
                "authDomain": getattr(self.env, "FIREBASE_WEB_AUTH_DOMAIN", "") or "",
                "projectId": getattr(self.env, "FIREBASE_WEB_PROJECT_ID", "") or "",
                "messagingSenderId": getattr(self.env, "FIREBASE_WEB_MESSAGING_SENDER_ID", "") or "",
                "appId": getattr(self.env, "FIREBASE_WEB_APP_ID", "") or "",
            }
            body = "self.TIANA_FIREBASE_CONFIG = " + json.dumps(config) + ";"
            return Response(body, headers={
                "Content-Type": "application/javascript; charset=utf-8",
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            })

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

        # The Django WSGI application is restored from the module-level Worker
        # snapshot, so normal requests do not perform Django setup again.
        return await wsgi.fetch(_application, request, self.env)
