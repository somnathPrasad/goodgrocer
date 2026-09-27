from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB, admin, session_for
from app.core.config import get_settings
from app.core.errors import DomainError
from app.schemas.domain import LoginInput, TokenResponse
from app.services import auth

router = APIRouter(prefix="/api/v1")
owner = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(admin)], tags=["admin"])


@router.post("/admin/auth/login", tags=["admin-auth"])
def admin_login(
    data: LoginInput,
    request: Request,
    response: Response,
    db: Session = TRANSACTIONAL_DB,
):
    if request.headers.get("origin") != get_settings().admin_origin:
        raise DomainError("FORBIDDEN", "Untrusted request origin", 403)
    result = auth.admin_login(db, data.username, data.password, request.client.host)
    response.set_cookie(
        "gg_admin",
        result["token"],
        httponly=True,
        secure=get_settings().environment == "production",
        samesite="strict",
        max_age=43200,
        path="/api/v1/admin",
    )
    return {"message": "Signed in"}


@router.post("/admin/auth/mobile-login", response_model=TokenResponse, tags=["admin-auth"])
def admin_mobile_login(data: LoginInput, request: Request, db: Session = TRANSACTIONAL_DB):
    if request.headers.get("origin"):
        raise DomainError("FORBIDDEN", "Use the browser sign-in endpoint", 403)
    return auth.admin_login(db, data.username, data.password, request.client.host)


@owner.post("/auth/logout", status_code=204)
def admin_logout(request: Request, response: Response, db: Session = TRANSACTIONAL_DB):
    auth.logout(db, session_for(request, db, True))
    response.delete_cookie("gg_admin", path="/api/v1/admin")


@owner.get("/me")
def admin_me():
    return {"authenticated": True}
