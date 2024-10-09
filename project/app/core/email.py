from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from typing import List
import logging

from app.core import settings_env

# Initialize logger
logger = logging.getLogger(__name__)

settings = settings_env

conf = ConnectionConfig(
    MAIL_USERNAME="islambek040508@gmail.com",
    MAIL_FROM="islambek040508@gmail.com",
    MAIL_PASSWORD="rrpj wfxt prie bkvh",  # Consider using environment variables for sensitive data
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    MAIL_FROM_NAME=f"{settings.APP_NAME}",
    USE_CREDENTIALS=True
)

fm = FastMail(conf)

async def send_email(recipients: List[str], subject: str, context: dict, background_tasks: BackgroundTasks):
    logger.info(f"Preparing to send email to: {recipients} with subject: '{subject}'")
    
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=context,
        subtype=MessageType.plain
    )
    
    background_tasks.add_task(fm.send_message, message)
    logger.info("Email sending task added to background tasks.")
