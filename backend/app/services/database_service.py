from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database.models import UserLocation


class LocationNotFoundError(RuntimeError):
    pass


@dataclass
class DatabaseService:
    db: Session

    def get_saved_location(self, user_id: int, location_type: str) -> tuple[float, float]:
        user_location = self.db.query(UserLocation).filter(UserLocation.user_id == user_id).first()
        if not user_location:
            raise LocationNotFoundError(f"No saved locations found for user_id={user_id}")

        if location_type == "home":
            latitude = user_location.home_latitude
            longitude = user_location.home_longitude
        else:
            latitude = user_location.work_latitude
            longitude = user_location.work_longitude

        if latitude is None or longitude is None:
            raise LocationNotFoundError(f"Saved {location_type} location is missing for user_id={user_id}")

        return latitude, longitude
