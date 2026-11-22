"""Application settings, read from environment variables with safe defaults."""
import os
import secrets


def _env_bool(name, default="0"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _env_list(name):
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


class Settings:
    # Random per boot when not configured: nothing secret is stored in the code.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _env_bool("APP_DEBUG")
    HOST = os.environ.get("APP_HOST", "127.0.0.1")
    PORT = int(os.environ.get("APP_PORT", "5000"))
    AMBIENTE = os.environ.get("APP_ENV", "producao")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    # Empty => CORS headers are not sent (same-origin only).
    CORS_ORIGINS = _env_list("CORS_ORIGINS")
    # Empty => admin endpoints are disabled (403).
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    # Opt-in for the read-only SQL console at /admin/query.
    ALLOW_ADMIN_QUERY = _env_bool("ALLOW_ADMIN_QUERY")
