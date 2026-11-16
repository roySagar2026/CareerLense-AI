from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import clear_refresh_cookie, client_ip, get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.user import DeleteAccountRequest, PasswordChangeRequest, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_service.to_out(user)


@router.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_service.update_profile(db, user, body)
    db.commit()
    return user_service.to_out(user)


@router.post("/me/password", status_code=204)
def change_password(
    body: PasswordChangeRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_service.change_password(db, user, body, client_ip(request))
    db.commit()
    return Response(status_code=204)


@router.delete("/me/data", status_code=204)
def delete_my_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_service.delete_all_data(db, user)
    db.commit()
    return Response(status_code=204)


@router.delete("/me", status_code=204)
def delete_my_account(
    body: DeleteAccountRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_service.delete_account(db, user, body.password)
    db.commit()
    response = Response(status_code=204)
    clear_refresh_cookie(response)
    return response
