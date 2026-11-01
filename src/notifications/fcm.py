"""Firebase Cloud Messaging HTTP v1 sender. Credentials are supplied only via env secrets."""
import json
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


def _firebase_credentials():
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError("Firebase service account is not configured.")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Firebase service account JSON is invalid.") from exc
    from google.oauth2 import service_account
    credentials = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"],
    )
    return credentials, info.get("project_id")


def send_push_to_user(user, title, body, data=None):
    """Send best-effort FCM notifications to every active device for a user."""
    from notifications.models import PushDevice

    credentials, project_id = _firebase_credentials()
    if not project_id:
        raise RuntimeError("Firebase service account is missing project_id.")

    import google.auth.transport.requests
    import requests

    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)
    devices = list(PushDevice.objects.filter(user=user, is_active=True))
    sent = 0
    dead_tokens = []

    for device in devices:
        payload = {
            "message": {
                "token": device.token,
                "notification": {"title": str(title)[:200], "body": str(body)[:1000]},
                "data": {str(k): str(v)[:500] for k, v in (data or {}).items()},
                "webpush": {"headers": {"Urgency": "normal"}},
            }
        }
        response = requests.post(
            f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send",
            headers={"Authorization": f"Bearer {credentials.token}", "Content-Type": "application/json"},
            json=payload,
            timeout=8,
        )
        if response.status_code == 200:
            sent += 1
        elif response.status_code in (400, 404):
            try:
                error = response.json().get("error", {})
                details = json.dumps(error)
            except ValueError:
                details = ""
            if "UNREGISTERED" in details or "INVALID_ARGUMENT" in details or response.status_code == 404:
                dead_tokens.append(device.pk)
            logger.warning("FCM rejected a device token (status %s).", response.status_code)
        else:
            logger.warning("FCM delivery failed with status %s.", response.status_code)

    if dead_tokens:
        PushDevice.objects.filter(pk__in=dead_tokens).update(is_active=False)
    return {"devices": len(devices), "sent": sent, "disabled": len(dead_tokens)}
