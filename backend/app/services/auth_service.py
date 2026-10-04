import logging
import hashlib
import hmac
import secrets
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database.models import UserAccount, UserLocation
from app.services.mapbox_service import MapboxService, MapboxServiceError
from app.security import create_access_token

logger = logging.getLogger(__name__)


class AuthError(RuntimeError):
    pass


@dataclass
class AuthService:
    db: Session
    beta_access_pin: str
    mapbox_service: MapboxService

    def validate_beta_pin(self, pin: str) -> bool:
        if not self.beta_access_pin:
            raise AuthError("Beta access pin is not configured")
        return hmac.compare_digest(pin.strip(), self.beta_access_pin.strip())

    def register_user(self, username: str, password: str, home_address: str, work_address: str) -> UserAccount:
        normalized_username = username.strip().lower()
        if self.db.query(UserAccount).filter(UserAccount.username == normalized_username).first():
            raise AuthError("Username already exists")

        try:
            home_candidate = self.mapbox_service.geocode_place(home_address.strip())
            work_candidate = self.mapbox_service.geocode_place(work_address.strip())

            user = UserAccount(username=normalized_username, password_hash=self._hash_password(password))
            self.db.add(user)
            self.db.flush()

            user_location = UserLocation(
                user_id=user.id,
                home_latitude=home_candidate.latitude,
                home_longitude=home_candidate.longitude,
                work_latitude=work_candidate.latitude,
                work_longitude=work_candidate.longitude,
            )
            self.db.add(user_location)

            self.db.commit()
            self.db.refresh(user)
            return user
        except MapboxServiceError as exc:
            self.db.rollback()
            raise AuthError(f"Unable to geocode address: {exc}") from exc
        except Exception:
            self.db.rollback()
            raise

    def login_user(self, username: str, password: str) -> UserAccount:
        normalized_username = username.strip().lower()
        user = self.db.query(UserAccount).filter(UserAccount.username == normalized_username).first()
        if not user or not self._verify_password(password, user.password_hash):
            raise AuthError("Invalid username or password")
        return user

    def update_user_profile(self, user_id: int, home_address: str, work_address: str) -> UserAccount:
        user = self.db.query(UserAccount).filter(UserAccount.id == user_id).first()
        if not user:
            raise AuthError("User not found")

        try:
            home_candidate = self.mapbox_service.geocode_place(home_address.strip())
            work_candidate = self.mapbox_service.geocode_place(work_address.strip())

            user_location = self.db.query(UserLocation).filter(UserLocation.user_id == user_id).first()
            if not user_location:
                user_location = UserLocation(user_id=user_id)
                self.db.add(user_location)

            user_location.home_latitude = home_candidate.latitude
            user_location.home_longitude = home_candidate.longitude
            user_location.work_latitude = work_candidate.latitude
            user_location.work_longitude = work_candidate.longitude

            self.db.commit()
            self.db.refresh(user)
            return user
        except MapboxServiceError as exc:
            self.db.rollback()
            raise AuthError(f"Unable to geocode address: {exc}") from exc
        except Exception:
            self.db.rollback()
            raise

    def get_user_profile(self, user_id: int) -> dict:
        user = self.db.query(UserAccount).filter(UserAccount.id == user_id).first()
        if not user:
            raise AuthError("User not found")

        user_location = self.db.query(UserLocation).filter(UserLocation.user_id == user_id).first()

        home_address = None
        work_address = None

        if user_location:
            try:
                if user_location.home_latitude is not None and user_location.home_longitude is not None:
                    home_address = self.mapbox_service.reverse_geocode(
                        user_location.home_latitude, user_location.home_longitude
                    )
                if user_location.work_latitude is not None and user_location.work_longitude is not None:
                    work_address = self.mapbox_service.reverse_geocode(
                        user_location.work_latitude, user_location.work_longitude
                    )
            except MapboxServiceError as exc:
                logger.warning(f"Reverse geocoding failed: {exc}")

        return {
            "user_id": user.id,
            "username": user.username,
            "home_address": home_address,
            "work_address": work_address,
        }

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

    def create_token(self, user: UserAccount) -> str:
        return create_access_token(user.id, user.username)