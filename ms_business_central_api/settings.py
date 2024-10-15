"""
Django settings for ms_business_central_api project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
import sys

import dj_database_url

from ms_business_central_api.sentry import Sentry

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.environ.get('DEBUG') == 'True' else False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(',')

ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Installed Apps
    'rest_framework',
    'corsheaders',
    'django_q',
    'fyle_rest_auth',
    'fyle_accounting_mappings',

    # User Created Apps
    'apps.users',
    'apps.workspaces',
    'apps.fyle',
    'apps.business_central',
    'apps.accounting_exports',
    'apps.mappings'
]

MIDDLEWARE = [
    'request_logging.middleware.LoggingMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "ms_business_central_api.logging_middleware.ErrorHandlerMiddleware",
]

ROOT_URLCONF = "ms_business_central_api.urls"
APPEND_SLASH = False

AUTH_USER_MODEL = 'users.User'

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

FYLE_REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'apps.users.serializers.UserSerializer'
}

FYLE_REST_AUTH_SETTINGS = {
    'async_update_user': True
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        # 'apps.workspaces.permissions.WorkspacePermissions'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'fyle_rest_auth.authentication.FyleJWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

SERVICE_NAME = os.environ.get('SERVICE_NAME')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '{levelname} %s {asctime} {module} {message} ' % SERVICE_NAME,
            'style': '{',
        },
        'requests': {
            'format': 'request {levelname} %s {asctime} {message}' % SERVICE_NAME,
            'style': '{'
        },
        "standard": {
            "format": "{levelname} %s {asctime} {name} {message}" % SERVICE_NAME,
            "style": "{",
        },
    },
    'handlers': {
        'debug_logs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose'
        },
        'request_logs': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'requests'
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    'loggers': {
        'django': {
            'handlers': ['request_logs'],
            'propagate': True,
        },
        'django.request': {
            'handlers': ['request_logs'],
            'propagate': False
        },
        'fyle_sage_desktop_api': {
            'handlers': ['debug_logs'],
            'level': 'ERROR',
            'propagate': False
        },
        'apps': {
            'handlers': ['debug_logs'],
            'level': 'ERROR',
            'propagate': False
        },
         'django_q': {
            'handlers': ['debug_logs'],
            'propagate': True,
        },
        'fyle_integrations_platform_connector': {
            'handlers': ['debug_logs'],
            'propagate': True,
        },
        'gunicorn': {
            'handlers': ['request_logs'],
            'level': 'INFO',
            'propagate': False
        },
        "dynamics.apis.api_base": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True
        },
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'auth_cache',
    }
}

Q_CLUSTER = {
    'name': 'ms_business_central_api',
    'save_limit': 0,
    'retry': 14400,
    'timeout': 3600,
    'catch_up': False,
    'workers': 4,
    # How many tasks are kept in memory by a single cluster.
    # Helps balance the workload and the memory overhead of each individual cluster
    'queue_limit': 10,
    'cached': False,
    'orm': 'default',
    'ack_failures': True,
    'poll': 5,
    'max_attempts': 1,
    'attempt_count': 1,
    # The number of tasks a worker will process before recycling.
    # Useful to release memory resources on a regular basis.
    'recycle': 50,
    # The maximum resident set size in kilobytes before a worker will recycle and release resources.
    # Useful for limiting memory usage.
    'max_rss': 100000  # 100mb
}


WSGI_APPLICATION = 'ms_business_central_api.wsgi.application'

SERVICE_NAME = os.environ.get('SERVICE_NAME')


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config()
}

DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True

DATABASES['cache_db'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'cache.db'
}

DATABASE_ROUTERS = ['ms_business_central_api.cache_router.CacheRouter']


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Fyle Settings
API_URL = os.environ.get('API_URL')
FYLE_TOKEN_URI = os.environ.get('FYLE_TOKEN_URI')
FYLE_CLIENT_ID = os.environ.get('FYLE_CLIENT_ID')
FYLE_CLIENT_SECRET = os.environ.get('FYLE_CLIENT_SECRET')
FYLE_BASE_URL = os.environ.get('FYLE_BASE_URL')
FYLE_JOBS_URL = os.environ.get('FYLE_JOBS_URL')
FYLE_APP_URL = os.environ.get('APP_URL')
FYLE_EXPENSE_URL = os.environ.get('FYLE_APP_URL')

# Business Central Settings
BUSINESS_CENTRAL_CLIENT_ID = os.environ.get("BUSINESS_CENTRAL_CLIENT_ID")
BUSINESS_CENTRAL_CLIENT_SECRET = os.environ.get("BUSINESS_CENTRAL_CLIENT_SECRET")
BUSINESS_CENTRAL_REDIRECT_URI = os.environ.get("BUSINESS_CENTRAL_REDIRECT_URI")
BUSINESS_CENTRAL_TOKEN_URI = os.environ.get("BUSINESS_CENTRAL_TOKEN_URI")
BUSINESS_CENTRAL_ENVIRONMENT = os.environ.get("BUSINESS_CENTRAL_ENVIRONMENT")

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

CORS_ORIGIN_ALLOW_ALL = True

# Sentry
Sentry.init()

CORS_ALLOW_HEADERS = ['sentry-trace', 'authorization', 'content-type']
