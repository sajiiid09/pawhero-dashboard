from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()

        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)

        server.send_message(msg)
        server.quit()
        logger.info("email sent to=%s subject=%s", to, subject)
    except Exception:
        logger.exception("email failed to=%s subject=%s", to, subject)
        raise


def build_reminder_email(
    owner_name: str,
    app_url: str,
    *,
    include_push_note: bool = True,
) -> tuple[str, str]:
    subject = "Pfoten-Held: Check-In erforderlich"
    push_note = (
        "\nZur gleichen Zeit wurde auch eine Push-Benachrichtigung "
        "fuer diesen Check-In ausgelost.\n"
        if include_push_note
        else ""
    )
    body = (
        f"Hallo {owner_name},\n\n"
        "dein naechster Check-In ist faellig. "
        "Bitte melde dich an und bestaetige jetzt, dass alles in Ordnung ist.\n\n"
        f"{push_note}"
        f"Dashboard: {app_url}/dashboard\n\n"
        "Wenn du nicht rechtzeitig reagierst, wird deine Notfallkette benachrichtigt.\n\n"
        "Dein Pfoten-Held Team"
    )
    return subject, body


def build_owner_escalation_email(
    owner_name: str,
    pet_name: str,
    app_url: str,
    public_profile_url: str,
) -> tuple[str, str]:
    subject = f"Pfoten-Held: Eskalation fuer {pet_name} gestartet"
    body = (
        f"Hallo {owner_name},\n\n"
        f"dein Check-In fuer {pet_name} wurde nicht bestaetigt. "
        "Die Notfallkette wurde gestartet.\n\n"
        f"Dashboard: {app_url}/dashboard\n"
        f"Oeffentliches Notfall-Profil: {public_profile_url}\n\n"
        "Bitte bestaetige deinen Status so schnell wie moeglich oder "
        "informiere deine Kontaktpersonen direkt.\n\n"
        "Pfoten-Held Notfall-System"
    )
    return subject, body


def build_emergency_contact_escalation_email(
    contact_name: str,
    owner_name: str,
    pet_name: str,
    public_profile_url: str,
    position: int,
    total: int,
) -> tuple[str, str]:
    subject = f"Pfoten-Held: Hilfe fuer {pet_name} benoetigt"
    body = (
        f"Hallo {contact_name},\n\n"
        f"{owner_name} hat auf keinen Check-In reagiert. "
        f"Du bist Kontakt {position} von {total} in der Notfallkette.\n\n"
        f"Bitte oeffne das Notfall-Profil fuer {pet_name}, "
        "pruefe die Hinweise und bestaetige dort, wenn du dich kuemmerst.\n\n"
        f"Notfall-Profil: {public_profile_url}\n\n"
        "Bitte versuche ausserdem, die Halterin oder den Halter direkt zu erreichen.\n\n"
        "Pfoten-Held Notfall-System"
    )
    return subject, body


def build_responder_ack_email(
    owner_name: str,
    responder_name: str,
    pet_name: str,
    app_url: str,
) -> tuple[str, str]:
    subject = f"Pfoten-Held: {responder_name} hat die Notfallbetreuung uebernommen"
    body = (
        f"Hallo {owner_name},\n\n"
        f"{responder_name} hat die Notfallbetreuung fuer {pet_name} uebernommen "
        "und wird sich um das Tier kuemmern.\n\n"
        f"Dashboard: {app_url}/dashboard\n\n"
        "Pfoten-Held Notfall-System"
    )
    return subject, body


def build_email_verification_otp_email(
    owner_name: str,
    otp_code: str,
    app_url: str,
    expires_minutes: int,
) -> tuple[str, str]:
    subject = "Pfoten-Held: Bestaetige deine E-Mail-Adresse"
    body = (
        f"Hallo {owner_name},\n\n"
        "willkommen bei Pfoten-Held. Bitte bestaetige deine E-Mail-Adresse mit "
        "dem folgenden Code:\n\n"
        f"{otp_code}\n\n"
        f"Der Code ist {expires_minutes} Minuten gueltig.\n\n"
        f"Zur Verifizierung: {app_url}/register/verify\n\n"
        "Falls du dich nicht registriert hast, kannst du diese E-Mail ignorieren.\n\n"
        "Dein Pfoten-Held Team"
    )
    return subject, body


def send_verification_email(
    to_email: str,
    owner_name: str,
    otp_code: str,
) -> None:
    settings = get_settings()
    subject, body = build_email_verification_otp_email(
        owner_name=owner_name,
        otp_code=otp_code,
        app_url=settings.app_url,
        expires_minutes=settings.email_verification_ttl_minutes,
    )
    send_email(to=to_email, subject=subject, body=body)
