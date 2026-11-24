from config.constants import DEFAULT_COLOR
from database import commit, db
from utils.time import utc_now


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
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
    def create(cls, name, description, color):
        category = cls(name=name, description=description, color=color)
        db.session.add(category)
        commit('Erro ao criar categoria')
        return category

    def update(self, fields):
        for name, value in fields.items():
            setattr(self, name, value)
        commit('Erro ao atualizar')
        return self

    def delete_detaching_tasks(self):
        """Delete the category and, in the same transaction, unlink its tasks (no orphan ids)."""
        for task in list(self.tasks):
            task.category_id = None
        db.session.delete(self)
        commit('Erro ao deletar')

    @classmethod
    def get_by_id(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_all(cls):
        return cls.query.all()

    @classmethod
    def count_all(cls):
        return cls.query.count()
