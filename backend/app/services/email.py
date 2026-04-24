from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from html import escape

from app.core.config import get_settings

logger = logging.getLogger(__name__)

BRAND_COLOR = "#5B8DEF"
TEXT_COLOR = "#1F2937"
MUTED_TEXT_COLOR = "#6B7280"
BACKGROUND_COLOR = "#F3F6FB"
CARD_COLOR = "#FFFFFF"
BORDER_COLOR = "#D9E4F7"
BUTTON_TEXT_COLOR = "#FFFFFF"


@dataclass(frozen=True)
class EmailContent:
    subject: str
    text_body: str
    html_body: str | None = None


def send_email(to: str, subject: str, body: str, html_body: str | None = None) -> None:
    settings = get_settings()

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    if html_body is not None:
        msg.add_alternative(html_body, subtype="html")

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
    check_in_url: str | None = None,
) -> EmailContent:
    subject = "Pfoten-Held: Check-In erforderlich"
    dashboard_url = f"{app_url}/dashboard"
    push_note_text = (
        "\nZur gleichen Zeit wurde auch eine Push-Benachrichtigung "
        "fuer diesen Check-In ausgelost.\n"
        if include_push_note
        else ""
    )
    check_in_link_text = ""
    if check_in_url:
        check_in_link_text = f"\nDirekt bestaetigen (ohne Anmeldung): {check_in_url}\n"

    text_body = (
        f"Hallo {owner_name},\n\n"
        "dein naechster Check-In ist faellig. "
        "Bitte melde dich an und bestaetige jetzt, dass alles in Ordnung ist.\n"
        f"{check_in_link_text}"
        f"{push_note_text}"
        f"Dashboard: {dashboard_url}\n\n"
        "Wenn du nicht rechtzeitig reagierst, wird deine Notfallkette benachrichtigt.\n\n"
        "Dein Pfoten-Held Team"
    )

    paragraphs = [
        "Dein naechster Check-In ist faellig. Bitte bestaetige jetzt, dass alles in Ordnung ist.",
        "Wenn du nicht rechtzeitig reagierst, wird deine Notfallkette benachrichtigt.",
    ]
    if include_push_note:
        paragraphs.insert(
            1,
            "Zur gleichen Zeit wurde auch eine Push-Benachrichtigung fuer diesen Check-In "
            "ausgeloest.",
        )

    html_body = _render_notification_email(
        eyebrow="Check-In",
        title="Bitte bestaetige deinen Status",
        greeting=f"Hallo {owner_name},",
        paragraphs=paragraphs,
        primary_action=(
            ("Jetzt direkt bestaetigen", check_in_url)
            if check_in_url is not None
            else ("Zum Dashboard", dashboard_url)
        ),
        secondary_links=[("Dashboard", dashboard_url)],
        footer="Dein Pfoten-Held Team",
    )
    return EmailContent(subject=subject, text_body=text_body, html_body=html_body)


def build_owner_escalation_email(
    owner_name: str,
    pet_name: str,
    app_url: str,
    public_profile_url: str,
    *,
    check_in_url: str | None = None,
) -> EmailContent:
    subject = f"Pfoten-Held: Eskalation fuer {pet_name} gestartet"
    dashboard_url = f"{app_url}/dashboard"
    check_in_link_text = ""
    if check_in_url:
        check_in_link_text = f"\nSofort quittieren (ohne Anmeldung): {check_in_url}\n"

    text_body = (
        f"Hallo {owner_name},\n\n"
        f"dein Check-In fuer {pet_name} wurde nicht bestaetigt. "
        "Die Notfallkette wurde gestartet.\n"
        f"{check_in_link_text}"
        f"\nDashboard: {dashboard_url}\n"
        f"Oeffentliches Notfall-Profil: {public_profile_url}\n\n"
        "Bitte bestaetige deinen Status so schnell wie moeglich oder "
        "informiere deine Kontaktpersonen direkt.\n\n"
        "Pfoten-Held Notfall-System"
    )

    html_body = _render_notification_email(
        eyebrow="Eskalation",
        title=f"Eskalation fuer {pet_name} gestartet",
        greeting=f"Hallo {owner_name},",
        paragraphs=[
            f"Dein Check-In fuer {pet_name} wurde nicht bestaetigt. Die Notfallkette wurde "
            "bereits gestartet.",
            "Bitte bestaetige deinen Status so schnell wie moeglich oder informiere deine "
            "Kontaktpersonen direkt.",
        ],
        primary_action=(
            ("Status sofort quittieren", check_in_url)
            if check_in_url is not None
            else ("Zum Dashboard", dashboard_url)
        ),
        secondary_links=[
            ("Dashboard", dashboard_url),
            ("Oeffentliches Notfall-Profil", public_profile_url),
        ],
        meta_rows=[("Tier", pet_name)],
        footer="Pfoten-Held Notfall-System",
    )
    return EmailContent(subject=subject, text_body=text_body, html_body=html_body)


def build_emergency_contact_escalation_email(
    contact_name: str,
    owner_name: str,
    pet_name: str,
    public_profile_url: str,
    position: int,
    total: int,
) -> EmailContent:
    subject = f"Pfoten-Held: Hilfe fuer {pet_name} benoetigt"
    text_body = (
        f"Hallo {contact_name},\n\n"
        f"{owner_name} hat auf keinen Check-In reagiert. "
        f"Du bist Kontakt {position} von {total} in der Notfallkette.\n\n"
        f"Bitte oeffne das Notfall-Profil fuer {pet_name}, "
        "pruefe die Hinweise und bestaetige dort, wenn du dich kuemmerst.\n\n"
        f"Notfall-Profil: {public_profile_url}\n\n"
        "Bitte versuche ausserdem, die Halterin oder den Halter direkt zu erreichen.\n\n"
        "Pfoten-Held Notfall-System"
    )

    html_body = _render_notification_email(
        eyebrow="Notfallkette",
        title=f"Hilfe fuer {pet_name} benoetigt",
        greeting=f"Hallo {contact_name},",
        paragraphs=[
            f"{owner_name} hat auf keinen Check-In reagiert. Bitte pruefe jetzt das "
            f"Notfall-Profil fuer {pet_name}.",
            "Bestaetige dort, wenn du dich kuemmern kannst, und versuche die Halterin oder "
            "den Halter direkt zu erreichen.",
        ],
        primary_action=("Notfall-Profil oeffnen", public_profile_url),
        meta_rows=[
            ("Tier", pet_name),
            ("Position in der Kette", f"{position} von {total}"),
        ],
        footer="Pfoten-Held Notfall-System",
    )
    return EmailContent(subject=subject, text_body=text_body, html_body=html_body)


def build_responder_ack_email(
    owner_name: str,
    responder_name: str,
    pet_name: str,
    app_url: str,
) -> EmailContent:
    subject = f"Pfoten-Held: {responder_name} hat die Notfallbetreuung uebernommen"
    dashboard_url = f"{app_url}/dashboard"
    text_body = (
        f"Hallo {owner_name},\n\n"
        f"{responder_name} hat die Notfallbetreuung fuer {pet_name} uebernommen "
        "und wird sich um das Tier kuemmern.\n\n"
        f"Dashboard: {dashboard_url}\n\n"
        "Pfoten-Held Notfall-System"
    )

    html_body = _render_notification_email(
        eyebrow="Rueckmeldung",
        title=f"{responder_name} kuemmert sich um {pet_name}",
        greeting=f"Hallo {owner_name},",
        paragraphs=[
            f"{responder_name} hat die Notfallbetreuung fuer {pet_name} uebernommen und "
            "wird sich um das Tier kuemmern."
        ],
        primary_action=("Zum Dashboard", dashboard_url),
        meta_rows=[("Tier", pet_name)],
        footer="Pfoten-Held Notfall-System",
    )
    return EmailContent(subject=subject, text_body=text_body, html_body=html_body)


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


def _render_notification_email(
    *,
    eyebrow: str,
    title: str,
    greeting: str,
    paragraphs: list[str],
    primary_action: tuple[str, str] | None = None,
    secondary_links: list[tuple[str, str]] | None = None,
    meta_rows: list[tuple[str, str]] | None = None,
    footer: str,
) -> str:
    paragraph_html = "".join(
        f'<p style="margin:0 0 16px;color:{TEXT_COLOR};font-size:16px;line-height:1.6;">'
        f"{escape(paragraph)}</p>"
        for paragraph in paragraphs
    )

    meta_html = ""
    if meta_rows:
        rows = "".join(
            f'<tr>'
            f'<td style="padding:0 12px 8px 0;color:{MUTED_TEXT_COLOR};font-size:13px;">'
            f"{escape(label)}</td>"
            f'<td style="padding:0 0 8px;color:{TEXT_COLOR};font-size:13px;font-weight:600;">'
            f"{escape(value)}</td>"
            f"</tr>"
            for label, value in meta_rows
        )
        meta_html = (
            f'<table role="presentation" cellspacing="0" cellpadding="0" '
            f'style="margin:0 0 20px;width:100%;">{rows}</table>'
        )

    primary_action_html = ""
    if primary_action is not None:
        label, url = primary_action
        primary_action_html = (
            f'<p style="margin:0 0 20px;">'
            f'<a href="{escape(url, quote=True)}" '
            f'style="display:inline-block;padding:12px 22px;background:{BRAND_COLOR};'
            f"color:{BUTTON_TEXT_COLOR};text-decoration:none;border-radius:999px;"
            f'font-size:15px;font-weight:700;">{escape(label)}</a></p>'
        )

    secondary_links_html = ""
    if secondary_links:
        items = "".join(
            f'<li style="margin:0 0 8px;">'
            f'<a href="{escape(url, quote=True)}" '
            f'style="color:{BRAND_COLOR};text-decoration:none;">{escape(label)}</a>'
            f"</li>"
            for label, url in secondary_links
        )
        secondary_links_html = (
            f'<div style="padding-top:16px;border-top:1px solid {BORDER_COLOR};">'
            f'<p style="margin:0 0 10px;color:{MUTED_TEXT_COLOR};font-size:13px;">'
            f"Weitere Links</p>"
            f'<ul style="margin:0;padding-left:18px;color:{BRAND_COLOR};">{items}</ul>'
            f"</div>"
        )

    return (
        f'<!doctype html><html lang="de"><body style="margin:0;padding:0;background:'
        f'{BACKGROUND_COLOR};font-family:Arial,sans-serif;">'
        f'<div style="padding:32px 16px;background:{BACKGROUND_COLOR};">'
        f'<table role="presentation" cellspacing="0" cellpadding="0" align="center" '
        f'style="width:100%;max-width:640px;border-collapse:collapse;">'
        f'<tr><td style="padding:0 0 16px;color:{BRAND_COLOR};font-size:13px;'
        f'font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">'
        f"Pfoten-Held</td></tr>"
        f'<tr><td style="background:{CARD_COLOR};border:1px solid {BORDER_COLOR};'
        f'border-radius:24px;padding:32px;">'
        f'<p style="margin:0 0 10px;color:{BRAND_COLOR};font-size:12px;font-weight:700;'
        f'letter-spacing:0.08em;text-transform:uppercase;">{escape(eyebrow)}</p>'
        f'<h1 style="margin:0 0 18px;color:{TEXT_COLOR};font-size:28px;line-height:1.2;">'
        f"{escape(title)}</h1>"
        f'<p style="margin:0 0 18px;color:{TEXT_COLOR};font-size:16px;line-height:1.6;">'
        f"{escape(greeting)}</p>"
        f"{meta_html}"
        f"{paragraph_html}"
        f"{primary_action_html}"
        f"{secondary_links_html}"
        f'<p style="margin:24px 0 0;color:{MUTED_TEXT_COLOR};font-size:13px;line-height:1.6;">'
        f"{escape(footer)}</p>"
        f"</td></tr></table></div></body></html>"
    )
