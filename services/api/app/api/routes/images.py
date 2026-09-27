from fastapi import APIRouter, Depends, UploadFile

from app.api.dependencies import admin
from app.services.providers import store_catalogue_image

router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(admin)], tags=["admin"])


@router.post("/images")
def upload(file: UploadFile):
    return {
        "image_url": store_catalogue_image(
            file.content_type,
            file.file.read(5 * 1024 * 1024 + 1),
        )
    }
