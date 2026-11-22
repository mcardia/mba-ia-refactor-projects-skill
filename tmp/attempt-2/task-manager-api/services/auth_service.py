"""Signed, expiring access tokens (replaces the guessable 'fake-jwt-token-<id>')."""
from itsdangerous import BadSignature, URLSafeTimedSerializer


class TokenService:
    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt='access-token')
        self._max_age = max_age_seconds

    def issue(self, user):
        return self._serializer.dumps({'uid': user.id})

    def verify(self, token):
        """Return the user id carried by a valid token, or None."""
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except BadSignature:  # also covers SignatureExpired
            return None
        return payload.get('uid') if isinstance(payload, dict) else None
