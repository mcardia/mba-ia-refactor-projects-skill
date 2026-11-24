import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import ROLE_USER
from database import commit, db
from utils.time import utc_now

_LEGACY_MD5 = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        # The password hash is never serialized.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    # ---- credentials --------------------------------------------------------------------
    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def verify_password(self, raw_password):
        """Constant-time check. Legacy unsalted MD5 hashes are accepted once and upgraded."""
        stored = self.password or ''
        if _LEGACY_MD5.match(stored):
            legacy = hashlib.md5(raw_password.encode()).hexdigest()  # read-only compatibility path
            if not hmac.compare_digest(stored, legacy):
                return False
            self.set_password(raw_password)
            commit('Erro ao atualizar')
            return True
        return check_password_hash(stored, raw_password)

    # ---- persistence --------------------------------------------------------------------
    @classmethod
    def create(cls, name, email, password, role):
        user = cls(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        commit('Erro ao criar usuário')
        return user

    def update(self, fields):
        password = fields.pop('password', None)
        for name, value in fields.items():
            setattr(self, name, value)
        if password is not None:
            self.set_password(password)
        commit('Erro ao atualizar')
        return self

    def delete_with_tasks(self):
        """Delete the user and its tasks in a single transaction."""
        for task in list(self.tasks):
            db.session.delete(task)
        db.session.delete(self)
        commit('Erro ao deletar')

    # ---- queries ------------------------------------------------------------------------
    @classmethod
    def get_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def list_all(cls):
        return cls.query.all()

    @classmethod
    def count_all(cls):
        return cls.query.count()
