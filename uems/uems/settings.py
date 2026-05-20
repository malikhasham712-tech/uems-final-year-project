"""
Django settings for uems project.
"""

from pathlib import Path

# ----------------------
# BASE DIRECTORY
# ----------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ----------------------
# SECURITY
# ----------------------
SECRET_KEY = 'django-insecure-l)qdv$kc40ro9&yjd6=$p&_fm6^b^22eii^v(r2ww1au1'

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "192.168.1.13"
]


# ----------------------
# CSRF FIX (🔥 IMPORTANT FOR MOBILE/LAN)
# ----------------------
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://192.168.1.10:8000"
]


# ----------------------
# SESSION FIX (🔥 MOBILE LOGIN STABILITY)
# ----------------------
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"


# ----------------------
# INSTALLED APPS
# ----------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps
    'accounts',
    'events',
    'core',
]


# ----------------------
# MIDDLEWARE
# ----------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ----------------------
# ROOT URL
# ----------------------
ROOT_URLCONF = 'uems.urls'


# ----------------------
# TEMPLATES
# ----------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # CUSTOM CONTEXT PROCESSOR
                'events.context_processors.notifications_context',
            ],
        },
    },
]


WSGI_APPLICATION = 'uems.wsgi.application'


# ----------------------
# DATABASE
# ----------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ----------------------
# PASSWORD VALIDATION
# ----------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ----------------------
# INTERNATIONALIZATION
# ----------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ----------------------
# STATIC FILES
# ----------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


# ----------------------
# DEFAULT PRIMARY KEY
# ----------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ----------------------
# EMAIL CONFIG
# ----------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'uemsproject@gmail.com'
EMAIL_HOST_PASSWORD = 'qpuumniyppqxmnhj'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# ----------------------
# LOGIN / LOGOUT
# ----------------------
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/events/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'