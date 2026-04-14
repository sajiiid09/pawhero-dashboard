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


def build_reminder_email(owner_name: str, app_url: str) -> tuple[str, str]:
    subject = "Pfoten-Held: Check-In erforderlich"
    body = (
        f"Hallo {owner_name},\n\n"
        "dein naechster Check-In ist faellig. "
        "Bitte melde dich an und bestaetige, dass alles in Ordnung ist.\n\n"
        f"Dashboard: {app_url}/dashboard\n\n"
        "Wenn du nicht rechtzeitig reagierst, wird deine Notfallkette benachrichtigt.\n\n"
        "Dein Pfoten-Held Team"
    )
    return subject, body


def build_escalation_email(
    contact_name: str,
    owner_name: str,
    app_url: str,
    position: int,
    total: int,
) -> tuple[str, str]:
    subject = f"Pfoten-Held: {owner_name} hat nicht reagiert"
    body = (
        f"Hallo {contact_name},\n\n"
        f"{owner_name} hat auf keinen Check-In reagiert. "
        f"Du bist Kontakt {position} von {total} in der Notfallkette.\n\n"
        "Bitte versuche, den Eigentmer zu erreichen oder nimm die notwendigen "
        "Schritte vor.\n\n"
        f"Dashboard: {app_url}/dashboard\n\n"
        "Pfoten-Held Notfall-System"
    )
    return subject, body
