"""
Django settings for sklandymas project.

Generated by 'django-admin startproject' using Django 2.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

from typing import List
import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    EMAIL_ENABLED=(bool, False),
    SENTRY_ENABLED=(bool, False),
    WEBTOPAY_TEST=(bool, True),
)
# reading .env file
environ.Env.read_env(env.str("ENV_PATH", "env"))
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS: List[str] = ["*"]


# Application definition

INSTALLED_APPS = [
    "coupons.apps.CouponsConfig",
    "crispy_forms",
    "crispy_bootstrap4",
    # "django_admin_shell",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "social_django",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)


ROOT_URLCONF = "sklandymas.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ]
        },
    }
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "coupons": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
# LOGIN_URL = '/dbadmin/login/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }
}

WSGI_APPLICATION = "sklandymas.wsgi.application"

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {"default": env.db("DATABASE_URL")}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
ATOMIC_REQUESTS = True

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "/login/google-oauth2"
LOGIN_REDIRECT_URL = "/admin/spawn"
LOGOUT_REDIRECT_URL = "/"
REDIRECT_IS_HTTPS = env.bool("ENABLE_HTTPS", False)


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Email
if env("EMAIL_ENABLED"):
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    ANYMAIL = {
        "MAILGUN_API_KEY": env("MAILGUN_ACCESS_KEY"),
        "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SERVER_NAME"),
    }
    MAILGUN_ACCESS_KEY = env("MAILGUN_ACCESS_KEY")
    MAILGUN_SERVER_NAME = env("MAILGUN_SERVER_NAME")
    DEFAULT_FROM_EMAIL = "Vilniaus Aeroklubas <aeroklubas@sklandymas.lt>"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Crispy forms
CRISPY_TEMPLATE_PACK = "bootstrap4"

# Coupons specific settings
COUPONS_HOME_URL = env("HOME_URL")
COUPONS_WEBTOPAY_PROJECT_ID = env("WEBTOPAY_PROJECT_ID")
COUPONS_WEBTOPAY_PASSWORD = env("WEBTOPAY_PASSWORD")
COUPONS_WEBTOPAY_TEST = env("WEBTOPAY_TEST")
COUPONS_EMAIL_SENDER = "Vilniaus Aeroklubas <aeroklubas@sklandymas.lt>"
COUPONS_EMAIL_REPLYTO = "Vilniaus Aeroklubas <aeroklubas@sklandymas.lt>"

if "BASE_URL" in env:
    CSRF_TRUSTED_ORIGINS = [env("BASE_URL")]

if env("SENTRY_ENABLED"):
    sentry_sdk.init(dsn=env("SENTRY_DSN"), integrations=[DjangoIntegration()])
