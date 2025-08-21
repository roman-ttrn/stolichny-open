print("🚀 LOADED DEV SETTINGS FILE")
from dotenv import load_dotenv
load_dotenv()
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

MEDIA_ROOT = BASE_DIR / 'media/'