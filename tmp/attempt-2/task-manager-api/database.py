import logging
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from utils.errors import ConflictError, PersistenceError

logger = logging.getLogger(__name__)

db = SQLAlchemy()


@event.listens_for(Engine, 'connect')
def _enable_sqlite_foreign_keys(dbapi_connection, _record):
    """SQLite ignores FOREIGN KEY constraints unless enabled per connection."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


def commit(error_message, conflict_message=None):
    """Commit the unit of work atomically; roll back everything on failure."""
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        if conflict_message:
            raise ConflictError(conflict_message) from exc
        logger.exception('Integrity error on commit')
        raise PersistenceError(error_message) from exc
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.exception('Database error on commit')
        raise PersistenceError(error_message) from exc
