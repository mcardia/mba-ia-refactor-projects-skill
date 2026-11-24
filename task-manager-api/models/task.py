from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from config.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING
from database import commit, db
from utils.time import utc_now


class Task(db.Model):
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

    # ---- domain rules -------------------------------------------------------------------
    def is_overdue(self, now=None):
        now = now or utc_now()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

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

    # ---- persistence --------------------------------------------------------------------
    @classmethod
    def create(cls, **fields):
        task = cls(**fields)
        db.session.add(task)
        commit('Erro ao criar task')
        return task

    def update(self, fields):
        for name, value in fields.items():
            setattr(self, name, value)
        self.updated_at = utc_now()
        commit('Erro ao atualizar')
        return self

    def delete(self):
        db.session.delete(self)
        commit('Erro ao deletar')

    # ---- queries ------------------------------------------------------------------------
    @classmethod
    def get_by_id(cls, task_id):
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
            pattern = f'%{text}%'  # bound as a parameter by SQLAlchemy
            query = query.filter(or_(cls.title.like(pattern), cls.description.like(pattern)))
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
    def _count_grouped(cls, *columns):
        rows = db.session.query(*columns, func.count(cls.id)).group_by(*columns).all()
        if len(columns) == 1:
            return {row[0]: row[1] for row in rows}
        return {tuple(row[:-1]): row[-1] for row in rows}

    @classmethod
    def count_by_status(cls):
        return cls._count_grouped(cls.status)

    @classmethod
    def count_by_priority(cls):
        return cls._count_grouped(cls.priority)

    @classmethod
    def count_by_user(cls):
        return cls._count_grouped(cls.user_id)

    @classmethod
    def count_by_category(cls):
        return cls._count_grouped(cls.category_id)

    @classmethod
    def count_by_user_and_status(cls):
        return cls._count_grouped(cls.user_id, cls.status)

    @classmethod
    def _overdue_query(cls, now):
        return cls.query.filter(
            cls.due_date.isnot(None),
            cls.due_date < now,
            or_(cls.status.is_(None), cls.status.notin_(CLOSED_STATUSES)),
        )

    @classmethod
    def list_overdue(cls, now):
        return cls._overdue_query(now).order_by(cls.id).all()

    @classmethod
    def count_overdue(cls, now):
        return cls._overdue_query(now).count()

    @classmethod
    def count_created_since(cls, since):
        return cls.query.filter(cls.created_at >= since).count()

    @classmethod
    def count_completed_since(cls, since):
        return cls.query.filter(cls.status == STATUS_DONE, cls.updated_at >= since).count()
