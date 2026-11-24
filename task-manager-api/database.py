import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from utils.errors import PersistenceError

logger = logging.getLogger(__name__)

db = SQLAlchemy()


def commit(error_message):
    """Commit the current unit of work atomically; roll back and raise a domain error on failure."""
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.exception('Database commit failed')
        raise PersistenceError(error_message) from exc
