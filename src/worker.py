"""Cloudflare Python Worker entry point for the TIANA Django app.

The Worker refuses to boot the finance app without PostgreSQL/Hyperdrive.
Static assets are served from the Worker Assets binding and uploaded media
from the dedicated R2 bucket binding.
"""
import asyncio
import os
from urllib.parse import unquote, urlsplit

from workers import Response, WorkerEntrypoint, wsgi

_application = None
# Python Workers can overlap requests while a synchronous DB driver is waiting
# on TCP. Serialize Django WSGI requests so a shared isolate never concurrently
# drives the same synchronous PostgreSQL connection.
_django_request_lock = asyncio.Lock()


def _copy_secret(env, source, target=None):
    value = getattr(env, source, None)
    if value is not None and str(value):
        os.environ[target or source] = str(value)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        global _application

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

        # Hyperdrive connectionString is an app secret; never return it in a response.
        hyperdrive = getattr(self.env, "HYPERDRIVE", None)
        connection_string = getattr(hyperdrive, "connectionString", None) if hyperdrive else None
        if not connection_string:
            return Response("TIANA staging database is not configured.", status=503)

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
        async with _django_request_lock:
            for source, target in required.items():
                _copy_secret(self.env, source, target)

            os.environ["DATABASE_URL"] = str(connection_string)
            os.environ["DEBUG"] = "0"
            os.environ["DB_CONN_MAX_AGE"] = "0"
            os.environ["DJANGO_DB_BACKEND"] = "nkem.db_backends.pg8000"
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nkem.settings")
            os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

            if not os.environ.get("SECRET_KEY") or not os.environ.get("ALLOWED_HOSTS"):
                return Response("TIANA staging security settings are incomplete.", status=503)

            if _application is None:
                from django.core.wsgi import get_wsgi_application
                _application = get_wsgi_application()

            return await wsgi.fetch(_application, request, self.env)
