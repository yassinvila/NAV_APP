from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas import NavigationRequest, NavigationResponse, ParsedCommand
from app.services.database_service import DatabaseService, LocationNotFoundError
from app.services.mapbox_service import MapboxService, MapboxServiceError, get_mapbox_service
from app.services.model_service import ModelService, ModelServiceError, get_model_service
from app.security import get_current_user, require_user

router = APIRouter(prefix="/navigation", tags=["navigation"])


def _build_destination_from_command(
    command: ParsedCommand,
    request_data: NavigationRequest,
    db_service: DatabaseService,
    mapbox_service: MapboxService,
    debug_trace: list[str],
) -> tuple[str, float, float]:
    if command.intent == "navigate_home":
        latitude, longitude = db_service.get_saved_location(request_data.user_id, "home")
        debug_trace.append("Resolved saved home location")
        return "Home", latitude, longitude

    if command.intent == "navigate_work":
        latitude, longitude = db_service.get_saved_location(request_data.user_id, "work")
        debug_trace.append("Resolved saved work location")
        return "Work", latitude, longitude

    if command.intent == "navigate_to_place":
        if not command.destination_name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="destination_name is required for navigate_to_place")
        try:
            candidate = mapbox_service.geocode_place(
                command.destination_name,
                request_data.current_location.latitude,
                request_data.current_location.longitude,
            )
            debug_trace.append(f"Mapbox place lookup: {candidate.name}")
            return candidate.name, candidate.latitude, candidate.longitude
        except MapboxServiceError:
            candidate = mapbox_service.geocode_place(command.destination_name)
            debug_trace.append(f"Mapbox fallback geocode: {candidate.name}")
            return candidate.name, candidate.latitude, candidate.longitude

    if command.intent == "navigate_to_category":
        if not command.destination_category:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="destination_category is required for navigate_to_category")
        try:
            candidate = mapbox_service.search_category(
                command.destination_category,
                request_data.current_location.latitude,
                request_data.current_location.longitude,
                command.selection_rule,
            )
            debug_trace.append(f"Mapbox category lookup: {candidate.name}")
            return candidate.name, candidate.latitude, candidate.longitude
        except MapboxServiceError:
            debug_trace.append("Category lookup failed, falling back to place search")
            if command.destination_category:
                candidate = mapbox_service.geocode_place(
                    command.destination_category,
                    request_data.current_location.latitude,
                    request_data.current_location.longitude,
                )
                debug_trace.append(f"Mapbox fallback place lookup: {candidate.name}")
                return candidate.name, candidate.latitude, candidate.longitude
            raise

    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported intent")


@router.post("/route", response_model=NavigationResponse)
def create_route(
    request_data: NavigationRequest,
    db: Session = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
    mapbox_service: MapboxService = Depends(get_mapbox_service),
    current_user=Depends(get_current_user),
) -> NavigationResponse:
    require_user(request_data.user_id, current_user)
    db_service = DatabaseService(db)
    model_key = request_data.model_key or "T5_NEMO"

    debug_trace: list[str] = [f"Model selected: {model_key}"]

    try:
        parsed_command, model_trace = model_service.parse_command_with_trace(request_data.text, model_key=model_key)
        debug_trace.extend(model_trace)
        destination_name, destination_latitude, destination_longitude = _build_destination_from_command(
            parsed_command,
            request_data,
            db_service,
            mapbox_service,
            debug_trace,
        )
        debug_trace.append("Calculating route to destination...")
        route = mapbox_service.route(
            (request_data.current_location.latitude, request_data.current_location.longitude),
            (destination_latitude, destination_longitude),
        )
        # Format route nicely: convert meters to km, seconds to minutes
        distance_km = round(route.get("distance", 0) / 1000, 1)
        duration_min = round(route.get("duration", 0) / 60)
        debug_trace.append(f"Route calculated: {distance_km} km, {duration_min} min")
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
            "debug_trace": debug_trace,
        }
    )
