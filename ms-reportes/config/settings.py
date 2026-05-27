"""Django settings for MS-7 Reportes & Estadísticas."""

import os
import sys
from pathlib import Path

from decouple import config

from config.agm_env import env_bool, cors_allowed_origins_list, mysql_database_settings

BASE_DIR = Path(__file__).resolve().parent.parent

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
    'apps.reportes',
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

SERVICE_NAME = config('SERVICE_NAME', default='ms-reportes')
USE_EVENT_BUS = config('USE_EVENT_BUS', default=True, cast=bool)
EVENT_QUEUE_NAME = config('EVENT_QUEUE_NAME', default='ms-reportes.events')
EVENT_CONTRACTS_DIR = config(
    'EVENT_CONTRACTS_DIR',
    default=str(BASE_DIR.parent.parent / 'contracts' / 'events'),
)

JWT_JWKS_URL = config(
    'JWT_JWKS_URL',
    default='http://ms-auth:8001/.well-known/jwks.json',
)
JWT_JWKS_CACHE_TTL_SECONDS = config('JWT_JWKS_CACHE_TTL_SECONDS', default=300, cast=int)
