"""
Django settings for Plataforma Estetica project.
"""
import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import dj_database_url

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_extensions',
    'django_filters',

    # Local apps (en orden de dependencias)
    'apps.empleados',  # PRIMERO - tiene Usuario, CentroEstetica, Sucursal
    'apps.clientes',
    'apps.servicios',
    'apps.turnos',
    'apps.inventario',
    'apps.finanzas',
    'apps.integraciones',  # Integraciones con sistemas externos (Conto)
    'apps.mi_caja',  # Sistema de punto de venta para empleados
    'apps.notificaciones',
    'apps.analytics',
    'apps.client_api',  # API para la app mobile de clientes
    'apps.public_api',  # API pública sin autenticación (info centro, catálogo)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serves static files in production
    'corsheaders.middleware.CorsMiddleware',  # CORS must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
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
        'DIRS': [],
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

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='postgresql://postgres:postgres@localhost:5432/plataforma_estetica'),
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Almacenamiento de archivos
#
# `default` sigue siendo el disco local a propósito: los cinco campos de archivo
# sensibles (fotos de clientas, antes/después, foto de usuario, comprobantes)
# no van a la nube todavía y necesitarían un bucket privado con URLs firmadas.
# Solo los dos campos públicos -- foto de producto y logo del centro -- optan
# explícitamente por el storage `publico`. Ver config/storage.py.
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

if AWS_STORAGE_BUCKET_NAME:
    STORAGES['publico'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'region_name': config('AWS_S3_REGION_NAME', default='sa-east-1'),
            # Las credenciales van explícitas y no por el entorno de boto3:
            # en desarrollo decouple las lee del .env, que boto3 no mira.
            'access_key': config('AWS_ACCESS_KEY_ID', default=None),
            'secret_key': config('AWS_SECRET_ACCESS_KEY', default=None),
            'querystring_auth': False,  # URLs limpias: el contenido es público
            'file_overwrite': False,    # dos subidas homónimas no se pisan
            'default_acl': None,        # los buckets nuevos tienen ACLs deshabilitadas
            # Se completa con el dominio de CloudFront cuando llegue: todas las
            # URLs cambian solas, sin tocar código.
            'custom_domain': config('AWS_S3_CUSTOM_DOMAIN', default=None) or None,
        },
    }
else:
    # Sin bucket configurado (desarrollo, tests, CI) el storage público cae al
    # disco local. Que no haya credenciales de AWS no puede romper el arranque.
    STORAGES['publico'] = {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    }

# Media files (User uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Auth de staff endurecida: rechaza tokens de la app mobile (token_use='cliente')
        'apps.empleados.authentication.StaffJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'config.pagination.FlexiblePageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'cliente_auth': '20/min',
        'cliente_registro': '10/hour',
        'cliente_reserva': '20/hour',
        'public_api': '100/hour',
        # El callback de OAuth de Tienda Nube dispara una llamada saliente por
        # visita. Una instalación real usa una sola.
        'tiendanube_oauth': '30/hour',
    },
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Spectacular (Swagger/OpenAPI) Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'Plataforma Estética API',
    'DESCRIPTION': 'API completa para gestión de centros de estética',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Redis & Celery Configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Push Notifications (Expo)
# Only needed if the Expo project has push security enabled; the Push API works
# unauthenticated otherwise.
EXPO_ACCESS_TOKEN = config('EXPO_ACCESS_TOKEN', default='')

# Delivery channel: 'expo' really sends, 'consola' prints instead. The console
# channel runs the whole pipeline -- triggers, queue, receipts, retries -- with
# no Expo account, no development build and no phone, which is how the system is
# exercised locally. Defaults to the console channel in DEBUG so a dev machine
# never sends a real notification by accident.
NOTIFICACIONES_CANAL = config(
    'NOTIFICACIONES_CANAL', default='consola' if DEBUG else 'expo'
)

# Logging
# Django's own defaults only surface WARNING and above from our code, which hid
# the console channel's simulated notifications and the queue run summaries.
# `disable_existing_loggers: False` keeps Django's default handlers intact.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '%(levelname)s %(name)s: %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'loggers': {
        'apps': {
            'handlers': ['console'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        # Los tracebacks de los errores 500 los emite Django por este logger.
        # Su configuración por defecto los manda al handler `mail_admins` y a
        # una consola filtrada con `require_debug_true`: en producción, donde
        # DEBUG es False y no hay ADMINS ni servidor de mail, eso significaba
        # que cada 500 se perdía sin dejar rastro en los logs.
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Daily skincare-routine reminder. Off by default: it is one push per day per
# client and the routine model still has no per-step frequency, so the reminder
# would be wrong for anything that is not meant to be done every night.
NOTIFICACIONES_RUTINA_DIARIA = config(
    'NOTIFICACIONES_RUTINA_DIARIA', default=False, cast=bool
)

# Custom User Model
AUTH_USER_MODEL = 'empleados.Usuario'

# Security Settings (for production)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_TRUSTED_ORIGINS = config(
        'CSRF_TRUSTED_ORIGINS',
        default='',
        cast=Csv()
    )

# Tienda Nube — credenciales de la app de partners.
# Salen de «Claves de Acceso» en el panel; solo se usan para emitir cupones
# (ver COMPRA_EN_APP_SPEC.md §5.1). Sin ellas la vinculación falla con un
# mensaje explícito en vez de intentar el intercambio.
TIENDANUBE_CLIENT_ID = config('TIENDANUBE_CLIENT_ID', default='')
TIENDANUBE_CLIENT_SECRET = config('TIENDANUBE_CLIENT_SECRET', default='')

# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_NUMBER = config('TWILIO_WHATSAPP_NUMBER', default='')  # Formato: +14155238886
TWILIO_WEBHOOK_BASE_URL = config('TWILIO_WEBHOOK_BASE_URL', default='')  # URL pública: https://tu-dominio.com
