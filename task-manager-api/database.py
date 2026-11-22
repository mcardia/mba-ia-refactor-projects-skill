import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from utils.errors import PersistenceError

db = SQLAlchemy()
logger = logging.getLogger(__name__)


class PersistenceMixin:
    """Unit-of-work helpers for models: stage changes, then call commit()."""

    def add(self):
        db.session.add(self)

    def remove(self):
        db.session.delete(self)

    def has_unsaved_changes(self):
        return db.session.is_modified(self)


def commit(error_message):
    """Commit the current unit of work atomically; roll back and raise on failure."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception('Database commit failed')
        raise PersistenceError(error_message)
