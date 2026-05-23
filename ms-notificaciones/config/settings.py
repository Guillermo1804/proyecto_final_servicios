"""Django settings for MS-6 Notificaciones."""

import os
import sys
from pathlib import Path

from decouple import config

from config.agm_env import env_bool, cors_allowed_origins_list, mysql_database_settings

BASE_DIR = Path(__file__).resolve().parent.parent

SERVICE_NAME = config('SERVICE_NAME', default='ms-notificaciones')
USE_EVENT_BUS = config('USE_EVENT_BUS', default=True, cast=bool)

JWT_JWKS_URL = config(
    'JWT_JWKS_URL',
    default='http://ms-auth:8001/.well-known/jwks.json',
)
JWT_JWKS_CACHE_TTL_SECONDS = config('JWT_JWKS_CACHE_TTL_SECONDS', default=300, cast=int)

# Stubs gRPC (import alumnos_pb2, auth_pb2, …)
sys.path.insert(0, os.path.join(BASE_DIR, 'proto_generated'))

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.notificaciones',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': mysql_database_settings()}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if env_bool('CORS_ALLOW_ALL_ORIGINS', default=True):
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = cors_allowed_origins_list()

# SMTP — django.core.mail (locmem/console en pruebas Docker)
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='AGM Sistema <noreply@agm.buap.mx>',
)

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'utils.exception_handlers.agm_exception_handler',
}

EVENT_QUEUE_NAME = config('EVENT_QUEUE_NAME', default='ms-notificaciones.events')
RABBITMQ_HOST = config('RABBITMQ_HOST', default='rabbitmq')
RABBITMQ_PORT = config('RABBITMQ_PORT', default='5672')
RABBITMQ_USER = config('RABBITMQ_USER', default='agm_bus')
RABBITMQ_PASSWORD = config('RABBITMQ_PASSWORD', default='agm_bus_dev_change_me')
RABBITMQ_VHOST = config('RABBITMQ_VHOST', default='agm')
EVENT_EXCHANGE = config('EVENT_EXCHANGE', default='agm.domain')
EVENT_PUBLISH_RETRIES = config('EVENT_PUBLISH_RETRIES', default=5, cast=int)
EVENT_PUBLISH_BACKOFF_SECONDS = config('EVENT_PUBLISH_BACKOFF_SECONDS', default=2, cast=float)
EVENT_CONSUME_MAX_RETRIES = config('EVENT_CONSUME_MAX_RETRIES', default=5, cast=int)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'apps.notificaciones.event_bus': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'agm_events': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
