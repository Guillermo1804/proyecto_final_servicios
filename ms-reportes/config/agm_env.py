"""Utilidades de entorno AGM (Epic 1 — Infra)."""
from decouple import config


def env_bool(key: str, default: bool = False) -> bool:
    raw = config(key, default=str(default))
    return str(raw).lower() in ('true', '1', 'yes')


def cors_allowed_origins_list() -> list[str]:
    raw = config('CORS_ALLOWED_ORIGINS', default='')
    return [o.strip() for o in raw.split(',') if o.strip()]


def mysql_database_settings() -> dict:
    return {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': config('DB_CHARSET', default='utf8mb4'),
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
