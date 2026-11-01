"""Serve non-secret Firebase Web SDK configuration to the same-origin service worker."""
import json
import os

from django.http import HttpResponse


def firebase_web_config_view(request):
    config = {
        "apiKey": os.environ.get("FIREBASE_WEB_API_KEY", ""),
        "authDomain": os.environ.get("FIREBASE_WEB_AUTH_DOMAIN", ""),
        "projectId": os.environ.get("FIREBASE_WEB_PROJECT_ID", ""),
        "messagingSenderId": os.environ.get("FIREBASE_WEB_MESSAGING_SENDER_ID", ""),
        "appId": os.environ.get("FIREBASE_WEB_APP_ID", ""),
    }
    # This is public Firebase web-app configuration, not the service-account secret.
    body = "self.TIANA_FIREBASE_CONFIG = " + json.dumps(config) + ";"
    response = HttpResponse(body, content_type="application/javascript; charset=utf-8")
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
