from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB, admin
from app.services import dashboard as dashboard_reporting

router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(admin)], tags=["admin"])


@router.get("/dashboard")
def dashboard(db: Session = TRANSACTIONAL_DB):
    return dashboard_reporting.owner_summary(db)
