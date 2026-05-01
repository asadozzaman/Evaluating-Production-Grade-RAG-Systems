from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, get_default_registration_role, require_roles
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, MessageResponse, TokenResponse, UserCreate, UserRead
from app.security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    existing_user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    role = get_default_registration_role(db)
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        roles=[role],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, user=user)


@router.post("/logout", response_model=MessageResponse)
def logout(_: Annotated[User, Depends(get_current_user)]) -> MessageResponse:
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.get("/admin-check", response_model=MessageResponse)
def admin_check(
    _: Annotated[User, Depends(require_roles(["admin"]))],
) -> MessageResponse:
    return MessageResponse(message="Admin access granted")


@router.get("/evaluator-check", response_model=MessageResponse)
def evaluator_check(
    _: Annotated[User, Depends(require_roles(["admin", "evaluator"]))],
) -> MessageResponse:
    return MessageResponse(message="Evaluator access granted")
