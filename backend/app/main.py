from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import models  # noqa: F401
from app.database.db import Base, engine
from app.routes.auth import router as auth_router
from app.routes.models import router as models_router
from app.routes.navigation import router as navigation_router
from app.rate_limit import RateLimitMiddleware

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.app_debug)
app.add_middleware(RateLimitMiddleware)
allow_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
if not allow_origins:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(models_router)
app.include_router(navigation_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
