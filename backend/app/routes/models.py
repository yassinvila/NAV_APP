from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.services.model_service import ModelService, ModelServiceError, get_model_service

router = APIRouter(prefix="/models", tags=["models"])


@router.post("/warmup")
def warm_up_model(
    model_key: Literal["T5_NEMO", "T5_CLAUDE"] = Query("T5_NEMO"),
    model_service: ModelService = Depends(get_model_service),
) -> dict[str, dict[str, str]]:
    try:
        status = model_service.warm_up(model_key)
        return {model_key: {"status": status}}
    except ModelServiceError as exc:
        return {model_key: {"status": "error", "message": str(exc)}}
