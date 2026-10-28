"""
Django settings for Online_Exam_Portal project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdirectory'
BASE_DIR = Path(__file__).resolve().parent.parent



def _env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def _env_list(name):
    """Comma-separated environment variable -> list of non-empty strings."""
    return [item.strip() for item in os.getenv(name, '').split(',') if item.strip()]


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool('DJANGO_DEBUG', False)

# SECURITY WARNING: keep the secret key secret in production!
# Deployments MUST set DJANGO_SECRET_KEY; the fallback exists only so local runs and
# CI work without configuration. `manage.py check --deploy` flags the fallback (W009).
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY') or 'django-insecure-dev-key-do-not-use-in-production'

# Comma-separated host names, e.g. DJANGO_ALLOWED_HOSTS=exam.example.edu
# With DEBUG off Django rejects every request unless the host is listed here.
ALLOWED_HOSTS = _env_list('DJANGO_ALLOWED_HOSTS')

# Origins trusted for CSRF over HTTPS, e.g. https://exam.example.edu
CSRF_TRUSTED_ORIGINS = _env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Custom apps
    'core',
    'accounts',
    'exams',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Online_Exam_Portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'Online_Exam_Portal.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password storage (SEC-REQ-01, design spec 3.6): salted, one-way, slow hash only.
# PBKDF2 must stay first so new and re-hashed passwords never use a weaker algorithm.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # target of `manage.py collectstatic`

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'  # Will be updated based on user role
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Custom authentication backend
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Transport protection (SEC-REQ-04, design spec 3.6 / Fig. 3): HTTPS-only outside DEBUG.
# HTTP requests are redirected to HTTPS and cookies/credentials never travel in clear text.
# See docs/https_deployment.md for the deployment steps and the environment variables.
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Behind a TLS-terminating reverse proxy (nginx, a PaaS router) the app only sees plain
# HTTP, so SECURE_SSL_REDIRECT would loop forever. Set DJANGO_BEHIND_PROXY=true ONLY when
# the proxy overwrites X-Forwarded-Proto itself and the app is not reachable directly.
if _env_bool('DJANGO_BEHIND_PROXY', False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
