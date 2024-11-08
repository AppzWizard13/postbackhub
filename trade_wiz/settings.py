"""
Django settings for trade_wiz project.

Generated by 'django-admin startproject' using Django 5.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from decouple import config


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-f-lro%0yj$70!j=-abx!**fm058-xn!3m*$#q05awh=9b^1b8j'
DEBUG = config('DEBUG', default=False, cast=bool)
TESTMODE = config('TESTMODE', default=False, cast=bool)

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = ['https://https://postback-hub.onrender.com', "http://localhost:8001", "http://127.0.0.1:8001","https://fe6e-2401-4900-667d-5c74-8060-e727-ea6c-483b.ngrok-free.app"]

# Application definition
INSTALLED_APPS = [
    'account',
    'scheduler',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Specify ASGI application
ASGI_APPLICATION = 'trade_wiz.asgi.application'

# Channels layer settings
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # You can use Redis for production
    },
}

APPEND_SLASH=False


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trade_wiz.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
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


WSGI_APPLICATION = 'trade_wiz.wsgi.application'
AUTH_USER_MODEL = 'account.User'


# Database
# Conditional database configuration based on DEBUG mode
if TESTMODE:
    # Use SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Database configuration
    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.postgresql',
    #         'NAME': config('DB_NAME'),
    #         'USER': config('DB_USER'),
    #         'PASSWORD': config('DB_PASSWORD'),
    #         'HOST': config('DB_HOST'),
    #         'PORT': config('DB_PORT', cast=int),  # Cast port to integer
    #     }
    # }
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR /  'LIVEDB/tradewiz-live.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

LANGUAGE_CODE = 'en-us'

USE_I18N = True

TIME_ZONE = 'Asia/Kolkata'

USE_TZ = True

BROKERAGE_PARAMETER = "33"

TRIGGER_SLIPPAGE = "0.05"

DEV_ADMIN = 'Appz'

ACTIVE_TRADER = ['juztin', 'tradingwitch']

ACTING_ADMIN = 'vicky'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# MEDIAFILE
MEDIA_URL = '/media/'


MEDIA_DIRS = [ os.path.join(BASE_DIR, 'media') ]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
