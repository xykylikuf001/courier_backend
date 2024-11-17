from app.core.celery_app import celery_app
from app.utils.emails import send_reset_password_email, send_email_verification, send_password_change_verification


@celery_app.task(
    acks_late=True,
    max_retries=3, countdown=10, retry_backoff=True, retry_backoff_max=120,
    retry=True,
)
def send_reset_password_email_task(
        email: str,
        code: str,
) -> None:
    return send_reset_password_email(email=email, verification_code=code)


@celery_app.task(
    acks_late=True,
    max_retries=3, countdown=10, retry_backoff=True, retry_backoff_max=120,
    retry=True,
)
def send_email_verification_task(email: str, code: str) -> None:
    return send_email_verification(email, verification_code=code)


@celery_app.task(
    acks_late=True,
    max_retries=3, countdown=10, retry_backoff=True, retry_backoff_max=120,
    retry=True,
)
def send_password_change_verification_task(email: str, code: str) -> None:
    return send_password_change_verification(email, verification_code=code)
