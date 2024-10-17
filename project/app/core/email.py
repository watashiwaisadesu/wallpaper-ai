from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from typing import List
import logging

from app.core import settings_env

logger = logging.getLogger(__name__)

settings = settings_env

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL,
    MAIL_FROM=settings.MAIL,
    MAIL_PASSWORD=settings.MAIL_APP_PASSWORD,
    MAIL_PORT=587,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    MAIL_FROM_NAME=f"{settings.APP_NAME}",
    USE_CREDENTIALS=True
)

fm = FastMail(conf)


async def send_email(recipients: List[str], subject: str, context: dict, background_tasks: BackgroundTasks):

    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=context,
        subtype=MessageType.plain
    )

    try:
        background_tasks.add_task(fm.send_message, message)
        logger.info(f"Email scheduled to be sent to {recipients}. Subject: '{subject}'")
    except Exception as e:
        logger.exception("Failed to schedule email sending.")
