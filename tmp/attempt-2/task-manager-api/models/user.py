import hashlib
import hmac
import re

from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import ROLE_ADMIN, ROLE_USER
from database import db
from utils.time import utc_now

_LEGACY_MD5 = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # salted hash, never serialized
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # ---- domain rules -------------------------------------------------------------------------
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password; transparently upgrades legacy unsalted MD5 hashes on success."""
        if _LEGACY_MD5.match(self.password or ''):
            legacy = hashlib.md5(password.encode()).hexdigest()
            if not hmac.compare_digest(legacy, self.password):
                return False
            self.set_password(password)
            return True
        return check_password_hash(self.password, password)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    # ---- serialization ------------------------------------------------------------------------
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def to_public_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email}

    # ---- persistence --------------------------------------------------------------------------
    @classmethod
    def get(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def all(cls):
        return db.session.scalars(select(cls).order_by(cls.id)).all()

    @classmethod
    def count(cls):
        return db.session.scalar(select(func.count(cls.id)))

    @classmethod
    def find_by_email(cls, email):
        return db.session.scalars(select(cls).where(cls.email == email)).first()

    def add(self):
        db.session.add(self)

    def remove(self):
        db.session.delete(self)
