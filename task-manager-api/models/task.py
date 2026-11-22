from sqlalchemy import func
from sqlalchemy.orm import selectinload

from config.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING
from database import PersistenceMixin, db
from utils.time import utc_now


class Task(PersistenceMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # ----- entity rules -------------------------------------------------
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def is_overdue(self, now=None):
        now = now or utc_now()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def days_overdue(self, now=None):
        now = now or utc_now()
        return (now - self.due_date).days

    def touch(self):
        self.updated_at = utc_now()

    @staticmethod
    def tags_to_column(tags):
        return ','.join(tags) if isinstance(tags, list) else tags

    # ----- queries ------------------------------------------------------
    @classmethod
    def find(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls):
        return cls.query.options(selectinload(cls.user), selectinload(cls.category)).all()

    @classmethod
    def list_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = cls.query
        if text:
            pattern = f'%{text}%'
            query = query.filter(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.filter(cls.status == status)
        if priority is not None:
            query = query.filter(cls.priority == priority)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.all()

    @classmethod
    def count_all(cls):
        return cls.query.count()

    @classmethod
    def count_by(cls, column):
        """{value: count} for one column, in a single GROUP BY query."""
        rows = db.session.query(column, func.count(cls.id)).group_by(column).all()
        return {value: count for value, count in rows}

    @classmethod
    def count_by_status(cls):
        return cls.count_by(cls.status)

    @classmethod
    def count_by_priority(cls):
        return cls.count_by(cls.priority)

    @classmethod
    def count_by_user(cls):
        return cls.count_by(cls.user_id)

    @classmethod
    def count_by_category(cls):
        return cls.count_by(cls.category_id)

    @classmethod
    def count_done_by_user(cls):
        rows = (db.session.query(cls.user_id, func.count(cls.id))
                .filter(cls.status == STATUS_DONE).group_by(cls.user_id).all())
        return {user_id: count for user_id, count in rows}

    @classmethod
    def list_overdue(cls, now):
        return (cls.query
                .filter(cls.due_date.isnot(None), cls.due_date < now,
                        cls.status.notin_(CLOSED_STATUSES))
                .order_by(cls.id).all())

    @classmethod
    def count_created_since(cls, since):
        return cls.query.filter(cls.created_at >= since).count()

    @classmethod
    def count_done_since(cls, since):
        return cls.query.filter(cls.status == STATUS_DONE, cls.updated_at >= since).count()
