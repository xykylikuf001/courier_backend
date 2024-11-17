import emails
from pathlib import Path
from typing import Any, Dict, List

from emails.template import JinjaTemplate

from app.conf.config import settings
from app.utils.templating import templates


def send_email(
        emails_to: List[str],
        subject_template: str = "",
        html_template: str = "",
        environment: Dict[str, Any] = None,
) -> None:
    assert settings.EMAILS_ENABLED, "no provided configuration for email variables"
    if environment is None:
        environment = {}
    message = emails.Message(
        subject=JinjaTemplate(subject_template, environment=templates.env),
        html=JinjaTemplate(html_template, environment=templates.env),
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )

    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT, }

    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(
        to=emails_to, render=environment, smtp=smtp_options, set_mail_to=True
    )

    return response


def send_test_email(emails_to: List[str]) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "test_email.html") as f:
        template_str = f.read()
    return send_email(
        emails_to=emails_to,
        subject_template=subject,
        html_template=template_str,
        environment={
            "project_name": settings.PROJECT_NAME, "emails": emails_to
        },
    )


def send_reset_password_email(email: str, verification_code: str, ) -> None:
    project_name = settings.PROJECT_NAME

    subject = "%(project_name)s - Password recovery for user with email %(email)s" % {
        'project_name': project_name, 'email': email
    }
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "reset_password.html") as f:
        template_str = f.read()
    server_host = settings.SERVER_HOST
    return send_email(
        emails_to=[email],
        subject_template=subject,
        html_template=template_str,
        environment={
            "server_host": server_host,
            "project_name": project_name,
            "email": email,
            "verification_code": verification_code,
        },
    )


def send_email_verification(email_to: str, verification_code: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = "%(project_name)s - Email verification for user with email %(email)s" % {
        'project_name': project_name, 'email': email_to
    }
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "verify_email.html") as f:
        template_str = f.read()
    return send_email(
        emails_to=[email_to],
        subject_template=subject,
        html_template=template_str,
        environment={
            "project_name": settings.PROJECT_NAME,
            "email": email_to,
            "verification_code": verification_code
        },
    )


def send_password_change_verification(email_to: str, verification_code: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = "%(project_name)s - Password change verification for user with email %(email)s" % {
        'project_name': project_name, 'email': email_to
    }
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "verify_password.html") as f:
        template_str = f.read()
    return send_email(
        emails_to=[email_to],
        subject_template=subject,
        html_template=template_str,
        environment={
            "project_name": settings.PROJECT_NAME,
            "email": email_to,
            "verification_code": verification_code
        },
    )
