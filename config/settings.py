from pathlib import Path
from decouple import config  # lee el archivo .env
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD: Leemos las claves del archivo .env
SECRET_KEY = config("SECRET_KEY", default="django-insecure-key-dev")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",  # ✅ ojo: ahora con coma correcta
    "corsheaders",

    # Mis Apps (Arquitectura Modular)
    "core",
    "inventario",
    "reservas",
    "reportes",
    "notificaciones.apps.NotificacionesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    "corsheaders.middleware.CorsMiddleware",  # ✅ debe ir antes de CommonMiddleware
    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- BASE DE DATOS (POSTGRESQL / SQLITE) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# --- USUARIO PERSONALIZADO ---
AUTH_USER_MODEL = "core.User"

# ==============================================================================
# HASH DE CONTRASEÑAS (Argon2 recomendado)
# ==============================================================================
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",      # ✅ principal
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",      # fallback
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",  # legacy fallback
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher" # legacy fallback
]

# ==============================================================================
# VALIDACIÓN DE CONTRASEÑAS (SEGURIDAD MEJORADA)
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "core.validators.ComplexPasswordValidator"},
    {"NAME": "core.validators.NotSameAsOldPasswordValidator"},
]

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- ARCHIVOS MULTIMEDIA ---
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# Permite que el sitio se muestre en iframes (ojo: es riesgoso en producción)
X_FRAME_OPTIONS = "ALLOWALL"

# ==============================================================================
# ✅ DJANGO REST FRAMEWORK + JWT
# ==============================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # Si además quieres que el admin/sesiones funcionen en endpoints DRF basados en sesión:
        # "rest_framework.authentication.SessionAuthentication",
    ),
    # (Opcional) si quieres obligar login en TODO DRF por defecto:
    # "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ==============================================================================
# ✅ CORS (si usas React u otro frontend separado)
# ==============================================================================
# Opción rápida (dev): permitir todo
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]