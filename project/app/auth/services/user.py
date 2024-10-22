from fastapi import HTTPException, BackgroundTasks,  Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import logging

from app.db.models import User
from app.core import settings_env, hash_password, get_async_db, validate
from app.auth.services import email
from app.utils import USER_VERIFY_ACCOUNT, FORGOT_PASSWORD
from app.db.repositories import load_user, save, logout_user
from .token import _verify_user_token, get_token_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
settings = settings_env
logger = logging.getLogger(__name__)

async def create_user_service(data, background_tasks: BackgroundTasks, session):
    try:
        logger.debug(f"Checking if user exists with email: {data.email}")
        user_exist = await load_user(data.email, session)
        if user_exist:
            logger.warning(f"Attempt to create user failed: Email already exists - {data.email}")
            raise HTTPException(status_code=400, detail="Email already exists.")

        # Uncomment the password validation if necessary
        if not validate(data.password):
            logger.warning(f"Password validation failed for email: {data.email}")
            raise HTTPException(status_code=400, detail="Please create valid password!")

        user = User(
            name=data.name,
            email=data.email,
            password=hash_password(data.password),
            is_active=False
        )

        await save(user, session)

        logger.info(f"User created successfully: {data.email}")

        await email.send_account_verification_email(user, background_tasks=background_tasks)

        return user
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex  # Reraise to propagate the HTTP error

    except Exception as ex:
        logger.exception("An error occurred while creating a user.")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def activate_user_service(data, background_tasks: BackgroundTasks, session):
    try:
        logger.debug(f"Attempting to activate user with email: {data.email}")
        user = await load_user(data.email, session)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        await _verify_user_token(user, data.token, USER_VERIFY_ACCOUNT)

        user.is_active = True
        user.verified_at = datetime.utcnow()
        await save(user, session)

        logger.info(f"User activated successfully: {data.email}")
        await email.send_account_activation_confirmation_email(user, background_tasks=background_tasks)
        return user
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred during user activation: {http_ex.detail}")
        raise http_ex  # Reraise to propagate the HTTP error

    except Exception as ex:
        logger.exception("An error occurred while activating a user.")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def forgot_password_email_link(data, background_tasks, session):
    try:
        logger.debug(f"Attempting to send password reset email for user: {data.email}")
        user = await _get_user(data.email, session)
        if not user.password:  # Проверка только на None или пустую строку
            logger.warning(f"Password reset attempt for OAuth user: {data.email}")
            raise ValueError("OAuth users cannot reset their password")

        _validate_user_status(user)
        await email.send_password_reset_email(user, background_tasks)
        logger.info(f"Password reset email sent to: {data.email}")
    except ValueError as ve:
        logger.error(f"Error during password reset: {ve}")
        raise  # Reraise to propagate the ValueError

    except Exception as ex:
        logger.exception("An error occurred while processing password reset.")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def reset_user_password(data, session):

        logger.debug(f"Attempting to reset password for user: {data.email}")

        user = await _get_user(data.email, session)

        if not user:
            logger.warning(f"Invalid password reset attempt for non-existing user: {data.email}")
            raise HTTPException(status_code=400, detail="Invalid request")
        if not user.password:  # Проверка только на None или пустую строку
            logger.warning(f"Password reset attempt for OAuth user: {data.email}")
            raise ValueError("OAuth users cannot reset their password")

        _validate_user_status(user)

        # Проверка токена сброса пароля
        await _verify_user_token(user, data.token, FORGOT_PASSWORD)

        # Обновление пароля пользователя
        if not validate(data.password):
            logger.warning(f"Password validation failed for user: {data.email}")
            raise HTTPException(status_code=400, detail="Please create valid password!")
        user.password = hash_password(data.password)
        await save(user, session)
        logger.info(f"Password successfully reset for user: {data.email}")


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_db)):
    logger.debug("Fetching current user from token.")
    user = await get_token_user(token=token, session=session)
    if user:
        logger.info(f"User retrieved successfully: {user.email}")
        return user
    logger.warning("Token validation failed or user not found.")
    raise HTTPException(status_code=401, detail="Not authorized.")

async def logout_user_service(user, session):
    logger.info(f"Logging out user: {user.email}")
    return await logout_user(user,session)

async def oauth_fetch_user(token: str):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        logger.debug("Fetching user info from Google OAuth API.")
        response = await client.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
        data = response.json()
        name = data.get('name')
        email = data['email']
        logger.info(f"User fetched successfully from OAuth: {email}")
        return name, email

async def _get_user(email: str, session) -> User:
    logger.debug(f"Loading user with email: {email}")
    user = await load_user(email, session)

    if not user:
        logger.warning(f"User not found: {email}")
        raise HTTPException(status_code=404, detail=f"User not found: {email}")

    logger.info(f"User found: {user.email}")
    return user

def _validate_user_status(user: User):
    logger.debug(f"Validating user status for: {user.email}")

    if not user.verified_at:
        logger.warning(f"User not verified: {user.email}")
        raise HTTPException(status_code=400, detail="User is not verified.")

    if not user.is_active:
        logger.warning(f"User not active: {user.email}")
        raise HTTPException(status_code=400, detail="User is not active.")


