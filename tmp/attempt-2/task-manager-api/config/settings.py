"""Application settings, read from the environment (and from a local .env file, if present)."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _csv(value):
    return [item.strip() for item in value.split(',') if item.strip()]


class Settings:
    # Random per boot when unset: issued tokens stop working after a restart. Set it in production.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = os.environ.get('APP_DEBUG', '0') == '1'
    HOST = os.environ.get('APP_HOST', '127.0.0.1')
    PORT = int(os.environ.get('APP_PORT', '5000'))

    # Empty => no cross-origin access is granted.
    CORS_ORIGINS = _csv(os.environ.get('CORS_ORIGINS', ''))

    TOKEN_MAX_AGE_SECONDS = int(os.environ.get('TOKEN_MAX_AGE_SECONDS', str(8 * 60 * 60)))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
