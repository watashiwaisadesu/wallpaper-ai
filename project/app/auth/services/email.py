from fastapi import BackgroundTasks

from app.db.models import User
from app.utils import USER_VERIFY_ACCOUNT, FORGOT_PASSWORD
from app.core import send_email, hash_password, settings_env


settings = settings_env
SERVER = f"{settings.SERVER_HOST}/users"


async def send_account_verification_email(user: User, background_tasks: BackgroundTasks):
    string_context = user.get_context_string(context=USER_VERIFY_ACCOUNT)
    token = hash_password(string_context)
    
    activate_url = f"{SERVER}/verify?token={token}&email={user.email}"
    subject = f"Verify Your Account - {settings.APP_NAME}"
    data = (
        f"Dear {user.name},\n\n"
        f"Thank you for creating an account with {settings.APP_NAME}!\n\n"
        "To complete your registration, please verify your email address by clicking the link below:\n"
        f"{activate_url}\n\n"
        "If you did not create an account, please ignore this email.\n\n"
        "Best regards,\n"
        f"The {settings.APP_NAME} Team"
    )
    
    await send_email(
        recipients=[user.email],
        subject=subject,
        context=data,
        background_tasks=background_tasks
    )


async def send_account_activation_confirmation_email(user: User, background_tasks: BackgroundTasks):
    subject = f"Welcome to {settings.APP_NAME}!"
    data = (
        f"Dear {user.name},\n\n"
        f"Welcome to {settings.APP_NAME}! We're excited to have you on board.\n\n"
        "To get started, please log in to your account using the following link:\n"
        f"{SERVER}\n\n"
        "If you have any questions or need assistance, feel free to reach out to our support team.\n\n"
        "Best regards,\n"
        f"The {settings.APP_NAME} Team"
    )
    
    await send_email(
        recipients=[user.email],
        subject=subject,
        context=data,
        background_tasks=background_tasks
    )


async def send_password_reset_email(user: User, background_tasks: BackgroundTasks):
    string_context = user.get_context_string(context=FORGOT_PASSWORD)
    token = hash_password(string_context)
    reset_url = f"{SERVER}/reset-password?token={token}&email={user.email}"

    subject = f"Reset Your Password - {settings.APP_NAME}"
    data = (
        f"Dear {user.name},\n\n"
        "We received a request to reset your password. Click the link below to set a new password:\n"
        f"{reset_url}\n\n"
        "If you did not request a password reset, please ignore this email.\n\n"
        "Thank you,\n"
        f"The {settings.APP_NAME} Team"
    )
    
    await send_email(
        recipients=[user.email],
        subject=subject,
        context=data,
        background_tasks=background_tasks
    )

