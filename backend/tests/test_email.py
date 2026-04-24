from __future__ import annotations

from types import SimpleNamespace

from app.services.email import (
    build_emergency_contact_escalation_email,
    build_reminder_email,
    send_email,
)


class FakeSMTP:
    last_message = None

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def ehlo(self) -> None:
        return None

    def starttls(self) -> None:
        return None

    def login(self, user: str, password: str) -> None:
        self.user = user
        self.password = password

    def send_message(self, message) -> None:
        FakeSMTP.last_message = message

    def quit(self) -> None:
        return None


def test_send_email_plain_text_only(monkeypatch):
    FakeSMTP.last_message = None
    monkeypatch.setattr(
        "app.services.email.get_settings",
        lambda: SimpleNamespace(
            smtp_from="noreply@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="mailer",
            smtp_password="secret",
        ),
    )
    monkeypatch.setattr("app.services.email.smtplib.SMTP", FakeSMTP)

    send_email(
        to="owner@example.com",
        subject="Pfoten-Held: Test",
        body="Nur Text",
    )

    message = FakeSMTP.last_message
    assert message is not None
    assert not message.is_multipart()
    assert message.get_content_type() == "text/plain"
    assert "Nur Text" in message.get_content()


def test_send_email_adds_html_alternative(monkeypatch):
    FakeSMTP.last_message = None
    monkeypatch.setattr(
        "app.services.email.get_settings",
        lambda: SimpleNamespace(
            smtp_from="noreply@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="mailer",
            smtp_password="secret",
        ),
    )
    monkeypatch.setattr("app.services.email.smtplib.SMTP", FakeSMTP)

    send_email(
        to="owner@example.com",
        subject="Pfoten-Held: HTML",
        body="Text-Version",
        html_body="<html><body><p>HTML-Version</p></body></html>",
    )

    message = FakeSMTP.last_message
    assert message is not None
    assert message.is_multipart()
    parts = message.iter_parts()
    plain_part = next(parts)
    html_part = next(parts)
    assert plain_part.get_content_type() == "text/plain"
    assert "Text-Version" in plain_part.get_content()
    assert html_part.get_content_type() == "text/html"
    assert "HTML-Version" in html_part.get_content()


def test_build_reminder_email_includes_check_in_cta_html():
    content = build_reminder_email(
        "Sajid",
        "https://app.example.com",
        include_push_note=True,
        check_in_url="https://app.example.com/c/token-123",
    )

    assert content.html_body is not None
    assert "https://app.example.com/c/token-123" in content.html_body
    assert "Jetzt direkt bestaetigen" in content.html_body


def test_build_emergency_contact_escalation_email_includes_public_profile_cta_html():
    content = build_emergency_contact_escalation_email(
        contact_name="Alex",
        owner_name="Sajid",
        pet_name="Bello",
        public_profile_url="https://app.example.com/s/token-456",
        position=1,
        total=3,
    )

    assert content.html_body is not None
    assert "https://app.example.com/s/token-456" in content.html_body
    assert "Notfall-Profil oeffnen" in content.html_body
