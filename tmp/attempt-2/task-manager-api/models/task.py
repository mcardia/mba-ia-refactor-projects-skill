from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import selectinload

from config.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING
from database import db
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

    # Deleting a user deletes their tasks (same transaction); deleting a category detaches its tasks.
    user = db.relationship('User', backref=db.backref('tasks', cascade='all, delete-orphan'))
    category = db.relationship('Category', backref='tasks')

    # ---- domain rules -------------------------------------------------------------------------
    def is_overdue(self, now=None):
        now = now or utc_now()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def days_overdue(self, now=None):
        return ((now or utc_now()) - self.due_date).days

    def apply_changes(self, fields):
        for name, value in fields.items():
            setattr(self, name, value)
        self.updated_at = utc_now()

    # ---- serialization ------------------------------------------------------------------------
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

    def to_detail_dict(self):
        data = self.to_dict()
        data['overdue'] = self.is_overdue()
        return data

    def to_list_dict(self):
        data = self.to_detail_dict()
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_user_task_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # ---- persistence --------------------------------------------------------------------------
    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def all_with_relations(cls):
        query = select(cls).options(selectinload(cls.user), selectinload(cls.category)).order_by(cls.id)
        return db.session.scalars(query).all()

    @classmethod
    def for_user(cls, user_id):
        return db.session.scalars(select(cls).where(cls.user_id == user_id).order_by(cls.id)).all()

    @classmethod
    def search(cls, term=None, status=None, priority=None, user_id=None):
        query = select(cls)
        if term:
            pattern = f'%{term}%'  # bound parameter, never interpolated into SQL
            query = query.where(or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.scalars(query.order_by(cls.id)).all()

    @classmethod
    def overdue_candidates(cls):
        """Open tasks with a due date; is_overdue() decides on each one."""
        query = select(cls).where(cls.due_date.is_not(None), cls.status.not_in(CLOSED_STATUSES))
        return db.session.scalars(query.order_by(cls.id)).all()

    @classmethod
    def count(cls):
        return db.session.scalar(select(func.count(cls.id)))

    @classmethod
    def count_by(cls, column):
        rows = db.session.execute(select(column, func.count(cls.id)).group_by(column)).all()
        return {key: total for key, total in rows}

    @classmethod
    def count_by_status(cls):
        return cls.count_by(cls.status)

    @classmethod
    def count_by_priority(cls):
        return cls.count_by(cls.priority)

    @classmethod
    def count_by_category(cls):
        return cls.count_by(cls.category_id)

    @classmethod
    def totals_by_user(cls):
        """{user_id: (total_tasks, completed_tasks)} in one aggregate query."""
        done = func.sum(case((cls.status == STATUS_DONE, 1), else_=0))
        rows = db.session.execute(select(cls.user_id, func.count(cls.id), done).group_by(cls.user_id)).all()
        return {user_id: (total, completed or 0) for user_id, total, completed in rows}

    @classmethod
    def count_created_since(cls, since):
        return db.session.scalar(select(func.count(cls.id)).where(cls.created_at >= since))

    @classmethod
    def count_completed_since(cls, since):
        query = select(func.count(cls.id)).where(cls.status == STATUS_DONE, cls.updated_at >= since)
        return db.session.scalar(query)

    def add(self):
        db.session.add(self)

    def remove(self):
        db.session.delete(self)
