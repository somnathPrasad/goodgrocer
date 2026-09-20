import logging
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException

from app.api.router import api_router
from app.api.routes.v1 import router
from app.core.config import get_settings
from app.core.errors import DomainError

logger = logging.getLogger("goodgrocer")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.propagate = False


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="Goodgrocer API", version="1.0.0")
    application.include_router(api_router)
    application.include_router(router)
    if settings.image_storage_provider == "local":
        settings.media_dir.mkdir(parents=True, exist_ok=True)
        application.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

    @application.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "; ".join(
                        ".".join(str(x) for x in e["loc"][1:]) + ": " + e["msg"]
                        for e in exc.errors()
                    ),
                }
            },
        )

    @application.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "CONFLICT",
                    "message": "A duplicate or referenced record prevents this change.",
                }
            },
        )

    @application.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
        )

    @application.middleware("http")
    async def log_request(request: Request, call_next):
        request_id, start = uuid4().hex, monotonic()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Something went wrong. Please try again.",
                    }
                },
            )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            (monotonic() - start) * 1000,
        )
        return response

    return application


app = create_app()
