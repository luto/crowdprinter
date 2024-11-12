import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True
ALLOWED_HOSTS = ["*"]
DOWNLOAD_FILE_PREFIX = ""

SECRET_KEY = "testtesttesttesttest"

DATABASE = {
    "ENGINE": "django_prometheus.db.backends.sqlite3",  # Database engine
    "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
}

# allauth
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
LOGIN_REDIRECT_URL = "/"

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Mail
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
