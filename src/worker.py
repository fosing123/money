"""Cloudflare Python Worker entry point for the TIANA Django app.

Bindings are read only inside fetch handlers. Django initialization is attempted
once per isolate; a failed setup is recorded rather than re-entered on the next
request, which would trigger Django's "populate() isn't reentrant" exception.
"""
import asyncio
import json
import os
import traceback
from urllib.parse import unquote, urlsplit

from workers import Response, WorkerEntrypoint, wsgi

_application = None
_initialization_attempted = False
_startup_error = None

# A synchronous PostgreSQL driver must not be driven concurrently by requests
# sharing this isolate. Keep the WSGI request path serialized.
_django_request_lock = asyncio.Lock()
_initialization_lock = asyncio.Lock()


def _copy_secret(source_env, source, target=None):
    value = getattr(source_env, source, None)
    if value is not None and str(value):
        os.environ[target or source] = str(value)


async def _initialize_django(source_env):
    """Initialize Django once, after request-handler access to Worker bindings."""
    global _application, _initialization_attempted, _startup_error

    if _initialization_attempted:
        return

    async with _initialization_lock:
        if _initialization_attempted:
            return

        # Mark before importing Django. If setup raises, never call setup again
        # in this isolate: Django's app registry is not re-entrant.
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

        # Keep root-level public files out of Django's Python startup path.
        # The build step copies these files into the Cloudflare Assets directory.
        if path in {"/service-worker.js", "/robots.txt", "/favicon.ico"}:
            return await self.env.ASSETS.fetch(request)

        # Firebase Web configuration is public client configuration. Return it
        # from Worker bindings directly so service-worker installation does not
        # need to initialize the full Django application.
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

        async with _django_request_lock:
            await _initialize_django(self.env)

            if _application is None:
                print("TIANA request rejected because Django did not initialize.")
                return Response(
                    "TIANA is temporarily unavailable because Django failed to start. "
                    "Check the Worker Logs for the startup traceback.",
                    status=503,
                )

            return await wsgi.fetch(_application, request, self.env)
