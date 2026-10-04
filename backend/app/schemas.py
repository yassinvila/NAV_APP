from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


Intent = Literal[
    "navigate_to_place",
    "navigate_to_category",
    "navigate_home",
    "navigate_work",
]

Category = Literal[
    "restaurant",
    "cafe",
    "bar",
    "bakery",
    "meal_takeaway",
    "gas_station",
    "pharmacy",
    "hospital",
    "doctor",
    "supermarket",
    "convenience_store",
    "shopping_mall",
    "clothing_store",
    "electronics_store",
    "bank",
    "atm",
    "airport",
    "train_station",
    "subway_station",
    "transit_station",
    "taxi_stand",
    "gym",
    "park",
    "spa",
    "hair_care",
    "post_office",
    "police",
    "car_repair",
    "school",
    "university",
    "lodging",
    "tourist_attraction",
]

SelectionRule = Literal["nearest", "best", "unspecified"]


class Location(BaseModel):
    latitude: float
    longitude: float


class NavigationRequest(BaseModel):
    user_id: int
    text: str
    current_location: Location
    model_key: Optional[Literal["T5_NEMO", "T5_CLAUDE"]] = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text cannot be empty")
        return value


class BetaPinRequest(BaseModel):
    pin: str


class BetaPinResponse(BaseModel):
    access_granted: bool


class RegisterRequest(BaseModel):
    username: str
    password: str
    home_address: str
    work_address: str

    @field_validator("username")
    @classmethod
    def username_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("username cannot be empty")
        return value

    @field_validator("password")
    @classmethod
    def password_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("password cannot be empty")
        return value

    @field_validator("home_address")
    @classmethod
    def home_address_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("home_address cannot be empty")
        return value

    @field_validator("work_address")
    @classmethod
    def work_address_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("work_address cannot be empty")
        return value


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthUser(BaseModel):
    user_id: int
    username: str


class AuthResponse(BaseModel):
    user: AuthUser
    access_token: str
    token_type: str = "bearer"


class ParsedCommand(BaseModel):
    intent: Intent
    destination_name: Optional[str] = None
    destination_category: Optional[str] = None  # Allow any string value for category
    selection_rule: SelectionRule = "unspecified"


class Destination(BaseModel):
    name: str
    latitude: float
    longitude: float


class RouteData(BaseModel):
    distance: float
    duration: float
    geometry: dict[str, Any]


class NavigationResponse(BaseModel):
    parsed_command: ParsedCommand
    destination: Destination
    route: RouteData
    debug_trace: list[str] = Field(default_factory=list)


class UpdateProfileRequest(BaseModel):
    user_id: int
    home_address: str
    work_address: str

    @field_validator("home_address")
    @classmethod
    def home_address_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("home_address cannot be empty")
        return value

    @field_validator("work_address")
    @classmethod
    def work_address_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("work_address cannot be empty")
        return value


class DestinationCandidate(BaseModel):
    name: str
    latitude: float
    longitude: float
    relevance: Optional[float] = None
    raw: dict[str, Any] = Field(default_factory=dict)
