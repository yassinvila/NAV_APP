from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.db import get_db
from app.schemas import AuthResponse, AuthUser, BetaPinRequest, BetaPinResponse, LoginRequest, RegisterRequest
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db=db, beta_access_pin=get_settings().beta_access_pin)


@router.post("/beta-pin", response_model=BetaPinResponse)
def validate_beta_pin(payload: BetaPinRequest, auth_service: AuthService = Depends(_auth_service)) -> BetaPinResponse:
    try:
        access_granted = auth_service.validate_beta_pin(payload.pin)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    if not access_granted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid beta access pin")

    return BetaPinResponse(access_granted=True)


@router.post("/register", response_model=AuthResponse)
def register_user(payload: RegisterRequest, auth_service: AuthService = Depends(_auth_service)) -> AuthResponse:
    try:
        user = auth_service.register_user(payload.username, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AuthResponse(user=AuthUser(user_id=user.id, username=user.username))


@router.post("/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, auth_service: AuthService = Depends(_auth_service)) -> AuthResponse:
    try:
        user = auth_service.login_user(payload.username, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return AuthResponse(user=AuthUser(user_id=user.id, username=user.username))