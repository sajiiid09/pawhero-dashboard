from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import DbSession
from app.db.models import Owner
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.services.auth import create_access_token, generate_id, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, session: DbSession) -> AuthResponse:
    existing = session.scalar(select(Owner).where(Owner.email == body.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Diese E-Mail-Adresse ist bereits registriert.",
        )

    owner = Owner(
        id=generate_id(),
        email=body.email,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
    )
    session.add(owner)
    session.commit()
    session.refresh(owner)

    token = create_access_token(owner.id)
    return AuthResponse(
        access_token=token,
        owner_id=owner.id,
        display_name=owner.display_name,
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, session: DbSession) -> AuthResponse:
    owner = session.scalar(select(Owner).where(Owner.email == body.email))
    if owner is None or not verify_password(body.password, owner.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungueltige Anmeldedaten.",
        )

    token = create_access_token(owner.id)
    return AuthResponse(
        access_token=token,
        owner_id=owner.id,
        display_name=owner.display_name,
    )
