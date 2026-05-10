import hashlib
import hmac
import secrets
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database.models import UserAccount


class AuthError(RuntimeError):
    pass


@dataclass
class AuthService:
    db: Session
    beta_access_pin: str

    def validate_beta_pin(self, pin: str) -> bool:
        if not self.beta_access_pin:
            raise AuthError("Beta access pin is not configured")
        return hmac.compare_digest(pin.strip(), self.beta_access_pin.strip())

    def register_user(self, username: str, password: str) -> UserAccount:
        normalized_username = username.strip().lower()
        if self.db.query(UserAccount).filter(UserAccount.username == normalized_username).first():
            raise AuthError("Username already exists")

        user = UserAccount(username=normalized_username, password_hash=self._hash_password(password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login_user(self, username: str, password: str) -> UserAccount:
        normalized_username = username.strip().lower()
        user = self.db.query(UserAccount).filter(UserAccount.username == normalized_username).first()
        if not user or not self._verify_password(password, user.password_hash):
            raise AuthError("Invalid username or password")
        return user

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return f"{salt}${derived_key.hex()}"

    def _verify_password(self, password: str, stored_password: str) -> bool:
        try:
            salt, password_hash = stored_password.split("$", 1)
        except ValueError:
            return False

        candidate_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return hmac.compare_digest(candidate_hash, password_hash)