from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    get_settings()

    application = FastAPI(title="Goodgrocer API", version="0.1.0")
    application.include_router(api_router)
    return application


app = create_app()
