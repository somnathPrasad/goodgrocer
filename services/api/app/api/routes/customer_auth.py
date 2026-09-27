from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies import (
    TRANSACTIONAL_DB,
    customer,
    optional_customer_id,
    session_for,
)
from app.models.domain import Customer
from app.schemas.domain import GoogleLoginInput, TokenResponse
from app.services import auth, customer_deletion

router = APIRouter(prefix="/api/v1")


@router.post("/auth/google", response_model=TokenResponse, tags=["auth"])
def google_login(data: GoogleLoginInput, request: Request, db: Session = TRANSACTIONAL_DB):
    return auth.google_login(db, data.id_token, request.client.host)


@router.post("/auth/logout", status_code=204, tags=["auth"])
def logout(
    request: Request,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    auth.logout(db, session_for(request, db, False))


@router.post("/account/deletion", status_code=204, tags=["auth"])
def delete_account(
    data: GoogleLoginInput,
    request: Request,
    db: Session = TRANSACTIONAL_DB,
):
    customer_deletion.delete_customer(
        db,
        data.id_token,
        request.client.host,
        optional_customer_id(request, db),
    )
