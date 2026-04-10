import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import environ

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------- ENTORNO ----------
APP_ENV = os.environ.get("APP_ENV", "dev").lower()  # "dev" | "prod"
IS_PROD = APP_ENV == "prod"

def _to_bool(v: str, default=False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key")
DEBUG = _to_bool(os.environ.get("DEBUG", "0" if IS_PROD else "1"))

ALLOWED_HOSTS = [
        ".onrender.com",
        "localhost",
        #"sicap.duckdns.org",
        "127.0.0.1",
        "sicap-app-o2eyd.ondigitalocean.app",
        ]

# Tu dominio del front (prod). Ej: https://sicap-frontend-mbn-yvqv.vercel.app
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "https://sicap-frontend-mbn-yvqv.vercel.app")

# ---------- APPS ----------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_filters",
    "storages",
    # apps
    "calles",
    "cargos",
    "cobrador",
    "colonia",
    "cuentahabientes",
    "descuento",
    "equipos",
    "pagos",
    "pagos_cargos",
    "servicio",
    "tesoreria",
    "corte",
]

# ---------- MIDDLEWARE ----------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",   # siempre antes de CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sicap_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sicap_backend.wsgi.application"

# ---------- STATIC ----------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------- DATABASE ----------
# ---------- DATABASE ----------
DB_URL_DEV = os.environ.get("DATABASE_URL_DEV") or os.environ.get("DATABASE_URL")
DB_URL_PROD = os.environ.get("DATABASE_URL_PROD")

CHOSEN_DB_URL = DB_URL_PROD if IS_PROD else DB_URL_DEV

DATABASES = {
    "default": dj_database_url.config(
        default=CHOSEN_DB_URL,
        conn_max_age=600,
        ssl_require=False  # SSL se maneja desde la URL con ?sslmode=
    )
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if "RENDER" not in os.environ:
    DATABASES["default"]["TEST"] = {"NAME": "test_mi_proyecto_db"}
    
# ---------- PASSWORDS ----------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------- I18N ----------
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- CORS / CSRF ----------
if IS_PROD:
    CORS_ALLOWED_ORIGINS = [FRONTEND_ORIGIN]
    CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://.*\.vercel\.app$"]
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        FRONTEND_ORIGIN,
    ]
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        r"^https://.*\.vercel\.app$"
    ]

CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com", "https://*.vercel.app"]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ["authorization", "content-type"]

# ---------- COOKIES / HTTPS ----------
SESSION_COOKIE_SECURE = IS_PROD
CSRF_COOKIE_SECURE = IS_PROD
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True  # (obsoleto pero inofensivo)
X_FRAME_OPTIONS = "DENY"

SECURE_SSL_REDIRECT = IS_PROD
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 if IS_PROD else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_PROD
SECURE_HSTS_PRELOAD = IS_PROD

# ---------- DRF ----------
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["cobrador.auth.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "120/min",
    },
}

# Desactiva BrowsableAPI en prod
if IS_PROD:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer",
    ]

# ---------- JWT ----------
JWT_SETTINGS = {
    "ACCESS_TOKEN_LIFETIME": 60 * 60 * 24,  # 1 día
    "ALGORITHM": "HS256",
    "SECRET": os.environ.get("JWT_SECRET", SECRET_KEY),
}

# ---------- LOGGING ----------
LOG_LEVEL = "INFO" if IS_PROD else "DEBUG"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {"simple": {"format": "[{levelname}] {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL},
        "django.server": {"handlers": ["console"], "level": LOG_LEVEL},
        "django.request": {"handlers": ["console"], "level": "WARNING" if IS_PROD else "INFO"},
        "urllib3": {"handlers": ["console"], "level": "WARNING"},
        "django.utils.autoreload": {
            "level": "INFO", 
        },
    },
}
env = environ.Env()
environ.Env.read_env()
# ─── DigitalOcean Spaces ──────────────────────────────────────────────────────

AWS_ACCESS_KEY_ID       = os.environ.get("DO_SPACES_KEY", "")
AWS_SECRET_ACCESS_KEY   = os.environ.get("DO_SPACES_SECRET", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("DO_SPACES_BUCKET", "")
AWS_S3_ENDPOINT_URL     = "https://sfo3.digitaloceanspaces.com"
AWS_S3_FILE_OVERWRITE   = False
AWS_DEFAULT_ACL         = "private"

DEFAULT_FILE_STORAGE     = "storages.backends.s3boto3.S3Boto3Storage"
MEDIA_URL                = "https://sicap-pdfs.sfo3.digitaloceanspaces.com/"