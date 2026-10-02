"""
Django settings for the Spotter fuel-route assessment.

This is plumbing - filled in so you don't burn time on it. The actual
assessment logic lives in route/services/ and route/views.py.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]  # TODO: tighten before you'd call this production-ready

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "route",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [],
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

# SQLite is fine for this assessment - no need to stand up Postgres for a
# take-home. Say so explicitly in your README so it reads as a decision,
# not an oversight.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []  # no user-facing auth needed for this assessment

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
}

# ---- Assessment-specific config -------------------------------------------
# TODO: pick your free routing provider (OSRM public demo / OpenRouteService)
# and put its base URL + key (if it needs one) here, read from env so you're
# not committing secrets.
ROUTING_API_BASE_URL = os.environ.get("ROUTING_API_BASE_URL", "")
ROUTING_API_KEY = os.environ.get("ROUTING_API_KEY", "")

# TODO: same for your geocoding provider, used only by the one-time
# management command - not called during a live request.
GEOCODING_API_BASE_URL = os.environ.get("GEOCODING_API_BASE_URL", "")

VEHICLE_RANGE_MILES = 500
VEHICLE_MPG = 10
