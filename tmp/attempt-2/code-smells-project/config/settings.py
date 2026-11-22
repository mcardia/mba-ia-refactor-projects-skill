"""Application settings, read from environment variables with development-safe defaults."""
import os
import secrets


def _env_bool(name, default="0"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _env_list(name):
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    # Random per boot when unset: never ship a real secret in source code.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _env_bool("APP_DEBUG")
    HOST = os.environ.get("APP_HOST", "127.0.0.1")
    PORT = int(os.environ.get("APP_PORT", "5000"))
    APP_ENV = os.environ.get("APP_ENV", "producao")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    # Comma-separated list of allowed origins; empty => cross-origin requests are not allowed.
    CORS_ORIGINS = _env_list("CORS_ORIGINS")
    # Empty => /admin/* endpoints are disabled (403).
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    # Explicit opt-in for the read-only /admin/query endpoint.
    ADMIN_SQL_QUERY_ENABLED = _env_bool("ADMIN_SQL_QUERY_ENABLED")
