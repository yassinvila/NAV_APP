from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.db import get_db
from app.schemas import AuthResponse, AuthUser, BetaPinRequest, BetaPinResponse, LoginRequest, RegisterRequest, UpdateProfileRequest
from app.services.mapbox_service import get_mapbox_service
from app.services.auth_service import AuthError, AuthService
from app.security import get_current_user, require_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_service(db: Session = Depends(get_db), mapbox_service=Depends(get_mapbox_service)) -> AuthService:
    return AuthService(db=db, beta_access_pin=get_settings().beta_access_pin, mapbox_service=mapbox_service)


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
        user = auth_service.register_user(
            payload.username,
            payload.password,
            payload.home_address,
            payload.work_address,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AuthResponse(
        user=AuthUser(user_id=user.id, username=user.username),
        access_token=auth_service.create_token(user),
    )


@router.post("/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, auth_service: AuthService = Depends(_auth_service)) -> AuthResponse:
    try:
        user = auth_service.login_user(payload.username, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return AuthResponse(
        user=AuthUser(user_id=user.id, username=user.username),
        access_token=auth_service.create_token(user),
    )


@router.patch("/profile", response_model=AuthResponse)
def update_profile(
    payload: UpdateProfileRequest,
    auth_service: AuthService = Depends(_auth_service),
    current_user=Depends(get_current_user),
) -> AuthResponse:
    require_user(payload.user_id, current_user)
    try:
        user = auth_service.update_user_profile(payload.user_id, payload.home_address, payload.work_address)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AuthResponse(
        user=AuthUser(user_id=user.id, username=user.username),
        access_token=auth_service.create_token(user),
    )


@router.get("/profile/{user_id}")
def get_profile(
    user_id: int,
    auth_service: AuthService = Depends(_auth_service),
    current_user=Depends(get_current_user),
):
    require_user(user_id, current_user)
    try:
        profile = auth_service.get_user_profile(user_id)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return profile
