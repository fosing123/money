"""Django settings for TIANA. Keep private credentials in the server environment."""
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import os

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

SOURCE_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = SOURCE_DIR.parent if SOURCE_DIR.name == "src" else SOURCE_DIR

# Neon CLI writes database credentials to .env.local. Load it first so
# its direct PostgreSQL URL is not hidden by a generic local .env file.
# Existing process environment variables retain highest priority.
for dotenv_file in (BASE_DIR / ".env.local", BASE_DIR / ".env"):
    if dotenv_file.is_file():
        load_dotenv(dotenv_file, override=False)


def env_bool(name, default=False):
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DEBUG", True)
CLOUDFLARE_WORKER = env_bool("CLOUDFLARE_WORKER", False)
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "local-development-only-not-for-production"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be configured for production.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must list the deployed TIANA hostnames.")

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "whitenoise.runserver_nostatic",
    "accounts", "core", "finance", "budgets", "goals", "insights",
    "ai_assistant", "expense_analyzer", "notifications", "marketplace",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    *([] if CLOUDFLARE_WORKER else ["whitenoise.middleware.WhiteNoiseMiddleware"]),
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "nkem.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [SOURCE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "core.context_processors.branding_context",
    ]},
}]
WSGI_APPLICATION = "nkem.wsgi.application"
ASGI_APPLICATION = "nkem.asgi.application"

# Prefer Neon’s direct endpoint for local Django/psycopg connections. The
# Worker replaces DATABASE_URL with Hyperdrive's connection string at runtime.
DATABASE_URL = (
    os.environ.get("DATABASE_URL_UNPOOLED")
    or os.environ.get("DATABASE_URL", "")
).strip()
if DATABASE_URL.startswith(("postgres://", "postgresql://")):
    parsed = urlparse(DATABASE_URL)
    params = parse_qs(parsed.query)
    database_backend = os.environ.get(
        "DJANGO_DB_BACKEND", "django.db.backends.postgresql"
    )
    if database_backend == "nkem.db_backends.pg8000":
        # Hyperdrive terminates TLS at its edge; pg8000 must use a plain
        # Worker TCP socket to the Hyperdrive endpoint.
        database_options = {"ssl_context": False}
    elif database_backend == "django.db.backends.postgresql":
        database_options = {
            "sslmode": params.get("sslmode", ["prefer" if DEBUG else "require"])[0]
        }
    else:
        raise ImproperlyConfigured(
            f"Unsupported PostgreSQL backend: {database_backend!r}"
        )
    DATABASES = {"default": {
        "ENGINE": database_backend,
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "localhost",
        "PORT": str(parsed.port or 5432),
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60" if DEBUG else "0")),
        "OPTIONS": database_options,
    }}
else:
    if not DEBUG:
        raise ImproperlyConfigured("Production TIANA requires PostgreSQL through Cloudflare Hyperdrive.")
    sqlite_path = DATABASE_URL.removeprefix("sqlite:///") if DATABASE_URL.startswith("sqlite:///") else "db.sqlite3"
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / sqlite_path, "CONN_MAX_AGE": 60}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Pyodide omits OpenSSL-backed hashlib.pbkdf2_hmac. Keep Django's standard
# PBKDF2-SHA256 storage format, but use a portable implementation on Workers.
PASSWORD_HASHERS = [
    "nkem.hashers.PortablePBKDF2PasswordHasher",
    "nkem.hashers.PortablePBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Douala"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "public" / "static"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": (
        {
            "BACKEND": "django_cf.storage.R2Storage",
            "OPTIONS": {
                "binding": "MEDIA",
                "location": "tiana-media",
                "allow_overwrite": False,
            },
        }
        if not DEBUG
        else {"BACKEND": "django.core.files.storage.FileSystemStorage"}
    ),
    "staticfiles": {
        # Cloudflare serves collected files through env.ASSETS, not from
        # STATIC_ROOT inside the Python runtime filesystem. Avoid WhiteNoise's
        # filesystem manifest lookup in that environment.
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG or CLOUDFLARE_WORKER
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/setup/"
LOGOUT_REDIRECT_URL = "/login/"
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "hello@tiana.app")

AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
AI_API_KEY = GEMINI_API_KEY or os.environ.get("AI_API_KEY", "")
AI_MODEL = GEMINI_MODEL

# AdSense remains disabled until Google approves the site and provides IDs.
ADSENSE_CLIENT_ID = os.environ.get("ADSENSE_CLIENT_ID", "ca-pub-1554607983371431").strip()
PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "https://tiana.lol").strip().rstrip("/")
ADSENSE_SLOT_ID = os.environ.get("ADSENSE_SLOT_ID", "").strip()
ADSENSE_ENABLED = ADSENSE_CLIENT_ID.startswith("ca-pub-") and ADSENSE_SLOT_ID.isdigit()

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
if not DEBUG:
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
