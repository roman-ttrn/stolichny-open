print("🔥 LOADED PROD SETTINGS FILE")

import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from .base import *

DEBUG = True
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

SECURE_HSTS_SECONDS = 31536000  # 1 год
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True  # Запрет доступа к кукам через JS
SESSION_COOKIE_SECURE = True    # Только HTTPS
SESSION_COOKIE_SAMESITE = 'Lax' # Защита от CSRF

X_FRAME_OPTIONS = 'DENY'

# Добавить прокси (если за Cloudflare/Nginx)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600

CSRF_TRUSTED_ORIGINS = [
    "https://stolichny.intellectum49.ru",
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # драйвер для PostgreSQL
        'NAME': os.getenv('POSTGRES_DB'),           # имя базы данных
        'USER': os.getenv('POSTGRES_USER'),         # пользователь PostgreSQL
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'), # пароль пользователя
        'HOST': os.getenv('POSTGRES_HOST', 'db'),   # хост (в docker-compose это имя сервиса)
        'PORT': os.getenv('POSTGRES_PORT', '5432'), # порт PostgreSQL
    }
}
