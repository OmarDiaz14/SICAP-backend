import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------- ENTORNO ----------
ENV = os.environ.get("ENV", "dev").lower()  # "dev" | "prod"
IS_PROD = ENV == "prod"

SECRET_KEY = os.environ["SECRET_KEY"] if IS_PROD else os.environ.get("SECRET_KEY", "dev-insecure-key")
DEBUG = os.environ.get("DEBUG", "0") == "1" if IS_PROD else True

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", ".onrender.com,localhost,127.0.0.1").split(",")

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
    # apps
    "asignaciones",
    "cargos",
    "cobrador",
    "colonia",
    "cuentahabientes",
    "descuento",
    "pagos",
    "sector",
    "servicio",
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
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
    )
}

# Render usa proxy; respeta cabecera X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if os.environ.get("RENDER", "") == "true":
    DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

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
    CORS_ALLOWED_ORIGIN_REGEXES = [r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", r"^https://.*\.vercel\.app$"]

CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com", "https://*.vercel.app"]

CORS_ALLOW_CREDENTIALS = True  # si usas cookies; con JWT por Authorization no es necesario
CORS_ALLOW_HEADERS = ["authorization", "content-type"]

# ---------- COOKIES / HTTPS ----------
SESSION_COOKIE_SECURE = IS_PROD
CSRF_COOKIE_SECURE = IS_PROD
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True  # (obsoleto pero no daña)
X_FRAME_OPTIONS = "DENY"

SECURE_SSL_REDIRECT = IS_PROD  # redirige HTTP -> HTTPS en prod
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 if IS_PROD else 0  # 1 semana; sube a 6 meses cuando esté estable
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_PROD
SECURE_HSTS_PRELOAD = IS_PROD

# ---------- DRF ----------
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["cobrador.auth.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    # throttle REAL (activas clases y ratios)
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        # opcional por IP:
        # "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "120/min",
        # "vista-pagos": "60/min",  # si usas ScopedRateThrottle por vista/acción
    },
}

# Desactiva BrowsableAPI en prod (evitas exponer data “bonita” en el navegador)
if IS_PROD:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer",
    ]

# ---------- JWT ----------
JWT_SETTINGS = {
    "ACCESS_TOKEN_LIFETIME": 60 * 60 * 24,  # 1 día
    "ALGORITHM": "HS256",
    # idealmente clave JWT separada de SECRET_KEY:
    "SECRET": os.environ.get("JWT_SECRET", SECRET_KEY),
}

# ---------- LOGGING ----------
# No loguees cuerpos de requests/responses ni variables sensibles en prod
LOG_LEVEL = "INFO" if IS_PROD else "DEBUG"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "formatters": {
        "simple": {"format": "[{levelname}] {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL},
        "django.server": {"handlers": ["console"], "level": LOG_LEVEL},
        # Evita verbosidad de drf/requests en prod
        "django.request": {"handlers": ["console"], "level": "WARNING" if IS_PROD else "INFO"},
        "urllib3": {"handlers": ["console"], "level": "WARNING"},
    },
}
