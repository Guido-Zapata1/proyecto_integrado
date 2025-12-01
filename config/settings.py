from pathlib import Path
from decouple import config  # <-- Esto lee el archivo .env

BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD: Leemos las claves del archivo .env
# IMPORTANTE: Si no tienes .env, DEBUG será False y las imágenes NO se verán.
SECRET_KEY = config('SECRET_KEY', default='django-insecure-key-dev')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    'corsheaders',
    # Mis Apps (Arquitectura Modular)
    'core',
    'inventario',
    'reservas',
    'reportes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # <--- ESTA ES LA LÍNEA CLAVE
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- BASE DE DATOS (POSTGRESQL) ---
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        # Configuración opcional para Postgres si usas .env
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default='', cast=str),
    }
}

# --- USUARIO PERSONALIZADO ---
AUTH_USER_MODEL = 'core.User'

# ==============================================================================
# VALIDACIÓN DE CONTRASEÑAS (SEGURIDAD MEJORADA)
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    # 1. Valida que no se parezca al nombre de usuario
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    # 2. Longitud mínima (8 caracteres)
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    # 3. Valida que no sea una contraseña común
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    # 4. Valida que no sea completamente numérica
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # 5. NUESTRO VALIDADOR PERSONALIZADO (Mayúsculas, Minúsculas, Números)
    {
        'NAME': 'core.validators.ComplexPasswordValidator',
    },
]

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS (CSS, JS, Imágenes del sistema) ---
STATIC_URL = 'static/'

# Dónde busca Django archivos estáticos en desarrollo (TU CARPETA MANUAL)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Dónde recolecta Django los estáticos para producción (AWS/Nginx)
# (Se genera solo al ejecutar python manage.py collectstatic)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# --- ARCHIVOS MULTIMEDIA (Subidos por el usuario, ej: fotos de recursos) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URL a donde se redirige si intentas entrar a una página privada sin loguearte
LOGIN_URL = 'login' 

# A dónde ir después de loguearse exitosamente
LOGIN_REDIRECT_URL = 'home'

# A dónde ir después de cerrar sesión
LOGOUT_REDIRECT_URL = 'login'

# Permite que el sitio se muestre en iframes (necesario para vista previa PDF)
X_FRAME_OPTIONS = 'ALLOWALL'