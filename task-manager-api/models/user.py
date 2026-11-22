import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import ROLE_USER
from database import PersistenceMixin, db
from utils.time import utc_now

_LEGACY_MD5 = re.compile(r'^[0-9a-f]{32}$')


class User(PersistenceMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        """Public representation; the password hash is never exposed."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, plain_password):
        self.password = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        """Verify a password; transparently upgrades legacy unsalted MD5 hashes.

        Returns True on success. The caller must commit to persist an upgraded hash.
        """
        stored = self.password or ''
        if _LEGACY_MD5.match(stored):
            legacy = hashlib.md5(plain_password.encode()).hexdigest()
            if hmac.compare_digest(stored, legacy):
                self.set_password(plain_password)
                return True
            return False
        return check_password_hash(stored, plain_password)

    # ----- queries ------------------------------------------------------
    @classmethod
    def find(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def list_all(cls):
        return cls.query.all()

    @classmethod
    def count_all(cls):
        return cls.query.count()

    def delete_with_tasks(self):
        """Delete the user and their tasks in the same unit of work (caller commits)."""
        for task in self.tasks:
            task.remove()
        self.remove()
