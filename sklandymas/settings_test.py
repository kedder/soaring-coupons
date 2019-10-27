from .settings import *

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
COUPONS_WEBTOPAY_PROJECT_ID = "test"
COUPONS_WEBTOPAY_PASSWORD = "pass"
