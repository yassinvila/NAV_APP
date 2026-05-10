from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas import NavigationRequest, NavigationResponse, ParsedCommand
from app.services.database_service import DatabaseService, LocationNotFoundError
from app.services.mapbox_service import MapboxService, MapboxServiceError, get_mapbox_service
from app.services.model_service import ModelService, ModelServiceError, get_model_service

router = APIRouter(prefix="/navigation", tags=["navigation"])


def _build_destination_from_command(
    command: ParsedCommand,
    request_data: NavigationRequest,
    db_service: DatabaseService,
    mapbox_service: MapboxService,
) -> tuple[str, float, float]:
    if command.intent == "navigate_home":
        latitude, longitude = db_service.get_saved_location(request_data.user_id, "home")
        return "Home", latitude, longitude

    if command.intent == "navigate_work":
        latitude, longitude = db_service.get_saved_location(request_data.user_id, "work")
        return "Work", latitude, longitude

    if command.intent == "navigate_to_place":
        if not command.destination_name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="destination_name is required for navigate_to_place")
        candidate = mapbox_service.geocode_place(command.destination_name)
        return candidate.name, candidate.latitude, candidate.longitude

    if command.intent == "navigate_to_category":
        if not command.destination_category:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="destination_category is required for navigate_to_category")
        candidate = mapbox_service.search_category(
            command.destination_category,
            request_data.current_location.latitude,
            request_data.current_location.longitude,
            command.selection_rule,
        )
        return candidate.name, candidate.latitude, candidate.longitude

    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported intent")


@router.post("/route", response_model=NavigationResponse)
def create_route(
    request_data: NavigationRequest,
    db: Session = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
    mapbox_service: MapboxService = Depends(get_mapbox_service),
) -> NavigationResponse:
    db_service = DatabaseService(db)

    try:
        parsed_command = model_service.parse_command(request_data.text)
        destination_name, destination_latitude, destination_longitude = _build_destination_from_command(
            parsed_command,
            request_data,
            db_service,
            mapbox_service,
        )
        route = mapbox_service.route(
            (request_data.current_location.latitude, request_data.current_location.longitude),
            (destination_latitude, destination_longitude),
        )
    except ModelServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MapboxServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return NavigationResponse.model_validate(
        {
            "parsed_command": parsed_command.model_dump(),
            "destination": {
                "name": destination_name,
                "latitude": destination_latitude,
                "longitude": destination_longitude,
            },
            "route": route,
        }
    )
