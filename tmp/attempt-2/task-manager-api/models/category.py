from sqlalchemy import func, select

from config.constants import DEFAULT_CATEGORY_COLOR
from database import db
from utils.time import utc_now


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_CATEGORY_COLOR)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @classmethod
    def get(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def all(cls):
        return db.session.scalars(select(cls).order_by(cls.id)).all()

    @classmethod
    def count(cls):
        return db.session.scalar(select(func.count(cls.id)))

    def add(self):
        db.session.add(self)

    def remove(self):
        """Delete the category; its tasks are detached (category_id = NULL) in the same transaction."""
        for task in self.tasks:
            task.category_id = None
        db.session.delete(self)
