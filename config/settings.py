import os
from pathlib import Path

from dotenv import load_dotenv
import dj_database_url

# Caminho base do projeto

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_LOGIN_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

# Segurança

SECRET_KEY = 'django-insecure-_vlajql=y5#3go@4su^x7mitxo)kxfbvn-cu9q65_b*p&en@1)'
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Apps instalados

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'quiz',
]

# Middlewares

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLs principais

ROOT_URLCONF = 'config.urls'

# Templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # opcional para templates globais
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'quiz.context_processors.theme_context',
            ],
        },
    },
]

# WSGI

WSGI_APPLICATION = 'config.wsgi.application'

# Banco de dados

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_SIGNUP_FIELDS = ['username*', 'password1*', 'password2*']

SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'prompt': 'select_account'},
    }
}

if GOOGLE_LOGIN_ENABLED:
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': GOOGLE_CLIENT_ID,
        'secret': GOOGLE_CLIENT_SECRET,
        'key': '',
    }

# Validação de senha

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

# Idioma e fuso

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True
USE_TZ = True

# Arquivos estáticos (CSS, JS, imagens, vídeos)

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Campo padrão do banco

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'