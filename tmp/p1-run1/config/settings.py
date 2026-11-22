"""Application settings, read from environment variables with safe development defaults."""
import os
import secrets


def _flag(name, default="0"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _list(name, default):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def load_settings():
    """Return the Flask config mapping. Read at app creation so tests can override env vars."""
    return {
        # Random per boot when unset: never a real secret in source code.
        "SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        "DEBUG": _flag("APP_DEBUG"),
        "HOST": os.environ.get("APP_HOST", "127.0.0.1"),
        "PORT": int(os.environ.get("APP_PORT", "5000")),
        "APP_ENV": os.environ.get("APP_ENV", "producao"),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO").upper(),
        "DATABASE_PATH": os.environ.get("DATABASE_PATH", "loja.db"),
        # Empty token => admin endpoints disabled (403).
        "ADMIN_TOKEN": os.environ.get("ADMIN_TOKEN", ""),
        # The raw read-only SQL console stays off unless explicitly enabled.
        "ADMIN_RAW_QUERY_ENABLED": _flag("ADMIN_RAW_QUERY_ENABLED"),
        "CORS_ORIGINS": _list("CORS_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000"),
    }
