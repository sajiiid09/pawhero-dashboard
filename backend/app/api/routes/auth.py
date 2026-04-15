from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import DbSession
from app.core.config import get_settings
from app.db.models import CheckInConfig, Owner
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    ResendOtpRequest,
    ResendOtpResponse,
    VerifyOtpRequest,
)
from app.services.auth import (
    compute_email_verification_expiry,
    create_access_token,
    generate_email_verification_code,
    generate_id,
    hash_email_verification_code,
    hash_password,
    verify_email_verification_code,
    verify_password,
)
from app.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


DEFAULT_CHECK_IN_INTERVAL_HOURS = 12
DEFAULT_ESCALATION_DELAY_MINUTES = 30
DEFAULT_PRIMARY_METHOD = "push"
DEFAULT_BACKUP_METHOD = "email"


def _ensure_default_check_in_config(session: DbSession, owner_id: str) -> None:
    existing = session.scalar(select(CheckInConfig).where(CheckInConfig.owner_id == owner_id))
    if existing is not None:
        return

    session.add(
        CheckInConfig(
            owner_id=owner_id,
            interval_hours=DEFAULT_CHECK_IN_INTERVAL_HOURS,
            escalation_delay_minutes=DEFAULT_ESCALATION_DELAY_MINUTES,
            primary_method=DEFAULT_PRIMARY_METHOD,
            backup_method=DEFAULT_BACKUP_METHOD,
            next_scheduled_at=datetime.now(UTC) + timedelta(hours=DEFAULT_CHECK_IN_INTERVAL_HOURS),
        )
    )


def _issue_email_verification(owner: Owner) -> str:
    verification_code = generate_email_verification_code()
    owner.email_verified = False
    owner.email_verification_code_hash = hash_email_verification_code(verification_code)
    owner.email_verification_expires_at = compute_email_verification_expiry()
    owner.email_verification_sent_at = datetime.now(UTC)
    return verification_code


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, session: DbSession) -> RegisterResponse:
    existing = session.scalar(select(Owner).where(Owner.email == body.email))
    if existing is not None and existing.email_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Diese E-Mail-Adresse ist bereits registriert.",
        )

    owner = existing
    if owner is None:
        owner = Owner(
            id=generate_id(),
            email=body.email,
            display_name=body.display_name,
            password_hash=hash_password(body.password),
            email_verified=False,
        )
        session.add(owner)
        _ensure_default_check_in_config(session, owner.id)
    else:
        owner.display_name = body.display_name
        owner.password_hash = hash_password(body.password)
        _ensure_default_check_in_config(session, owner.id)

    verification_code = _issue_email_verification(owner)
    session.flush()

    try:
        send_verification_email(
            to_email=owner.email,
            owner_name=owner.display_name,
            otp_code=verification_code,
        )
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verifizierungs-E-Mail konnte nicht gesendet werden. Bitte erneut versuchen.",
        ) from exc

    session.commit()

    return RegisterResponse(
        owner_id=owner.id,
        email=owner.email,
        display_name=owner.display_name,
        verification_required=True,
        message="Bitte OTP aus der E-Mail eingeben, um dein Konto zu aktivieren.",
    )


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(body: VerifyOtpRequest, session: DbSession) -> AuthResponse:
    owner = session.scalar(select(Owner).where(Owner.email == body.email))
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Konto nicht gefunden.",
        )

    if owner.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail-Adresse wurde bereits bestaetigt.",
        )

    if owner.email_verification_code_hash is None or owner.email_verification_expires_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine aktive OTP-Verifizierung gefunden. Bitte OTP erneut anfordern.",
        )

    now = datetime.now(UTC)
    if owner.email_verification_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP ist abgelaufen. Bitte OTP erneut anfordern.",
        )

    if not verify_email_verification_code(body.code.strip(), owner.email_verification_code_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP ist ungueltig.",
        )

    owner.email_verified = True
    owner.email_verification_code_hash = None
    owner.email_verification_expires_at = None
    owner.email_verification_sent_at = None
    session.commit()

    token = create_access_token(owner.id)
    return AuthResponse(
        access_token=token,
        owner_id=owner.id,
        display_name=owner.display_name,
    )


@router.post("/resend-otp", response_model=ResendOtpResponse)
def resend_otp(body: ResendOtpRequest, session: DbSession) -> ResendOtpResponse:
    owner = session.scalar(select(Owner).where(Owner.email == body.email))
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Konto nicht gefunden.",
        )

    if owner.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail-Adresse wurde bereits bestaetigt.",
        )

    settings = get_settings()
    now = datetime.now(UTC)
    if owner.email_verification_sent_at is not None:
        retry_after = settings.email_verification_resend_cooldown_seconds - int(
            (now - owner.email_verification_sent_at).total_seconds()
        )
        if retry_after > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Bitte in {retry_after} Sekunden erneut versuchen.",
            )

    verification_code = _issue_email_verification(owner)
    session.flush()

    try:
        send_verification_email(
            to_email=owner.email,
            owner_name=owner.display_name,
            otp_code=verification_code,
        )
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verifizierungs-E-Mail konnte nicht gesendet werden. Bitte erneut versuchen.",
        ) from exc

    session.commit()
    return ResendOtpResponse(message="Ein neues OTP wurde an deine E-Mail-Adresse gesendet.")


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, session: DbSession) -> AuthResponse:
    owner = session.scalar(select(Owner).where(Owner.email == body.email))
    if owner is None or not verify_password(body.password, owner.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungueltige Anmeldedaten.",
        )

    if not owner.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="E-Mail-Adresse ist noch nicht bestaetigt. Bitte OTP eingeben.",
        )

    token = create_access_token(owner.id)
    return AuthResponse(
        access_token=token,
        owner_id=owner.id,
        display_name=owner.display_name,
    )
