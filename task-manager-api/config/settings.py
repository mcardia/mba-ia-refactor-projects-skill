"""Application settings, read from environment variables (and an optional .env file)."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _csv(value):
    return [item.strip() for item in value.split(',') if item.strip()]


class Settings:
    # Random per boot when unset: issued tokens stop being valid after a restart.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = os.environ.get('APP_DEBUG', '0') == '1'
    HOST = os.environ.get('APP_HOST', '127.0.0.1')
    PORT = int(os.environ.get('APP_PORT', '5000'))

    # Empty list => no cross-origin access is granted.
    CORS_ORIGINS = _csv(os.environ.get('CORS_ORIGINS', ''))

    # Empty => privileged endpoints are disabled (403).
    ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')
