from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/api/v1")


@router.get("/config")
def config():
    settings = get_settings()
    return {
        "online_upi_enabled": False,
        "development": settings.environment != "production",
        "delivery_fee": str(settings.delivery_fee),
    }
