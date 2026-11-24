"""Application settings, read from environment variables (a local .env file is loaded if present)."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _env_list(name):
    value = os.environ.get(name, '')
    return [item.strip() for item in value.split(',') if item.strip()]


class Settings:
    # A random key per boot when SECRET_KEY is unset: safe default, but issued tokens die on restart.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SECRET_KEY_FROM_ENV = bool(os.environ.get('SECRET_KEY'))

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _env_bool('APP_DEBUG', False)
    HOST = os.environ.get('APP_HOST', '127.0.0.1')
    PORT = int(os.environ.get('APP_PORT', '5000'))

    # Comma-separated list of allowed browser origins; empty disables CORS headers entirely.
    CORS_ORIGINS = _env_list('CORS_ORIGINS')

    TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', '3600'))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
