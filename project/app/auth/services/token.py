from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
import logging

from app.db.models import User, UserToken
from app.core import get_token_payload, str_decode, str_encode, generate_token, settings_env, verify_password
from app.utils import unique_string
from app.db.repositories import save, get_user_token_by_keys, expire_delete

settings = settings_env
logger = logging.getLogger(__name__)

def _create_access_token(user: User, access_key: str, user_token: UserToken) -> str:
    at_payload = {
        "sub": str_encode(str(user.id)),
        'a_key': access_key,
        'ut_ID': str_encode(str(user_token.id)),
        'name': str_encode(user.name)
    }

    at_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = generate_token(at_payload, settings.JWT_SECRET, settings.JWT_ALGORITHM, at_expires)
    logger.debug(f"Access token created for user: {user.id}")
    return token


def _create_refresh_token(user: User, refresh_key: str, access_key: str) -> str:
    rt_payload = {
        "sub": str_encode(str(user.id)),
        "r_key": refresh_key,
        'a_key': access_key
    }
    rt_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    token = generate_token(rt_payload, settings.SECRET_KEY, settings.JWT_ALGORITHM, rt_expires)
    logger.debug(f"Refresh token created for user: {user.id}")
    return token


async def get_refresh_token(refresh_token, session):
    logger.debug("Attempting to refresh token.")
    token_payload = get_token_payload(refresh_token, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    if not token_payload:
        logger.warning("Invalid refresh token provided.")
        raise HTTPException(status_code=400, detail="Invalid Request.")

    user_token = await get_user_token_by_keys(
        refresh_key=token_payload.get('r_key'),
        access_key=token_payload.get('a_key'),
        user_id=str_decode(token_payload.get('sub')),
        session=session
    )

    if not user_token:
        logger.warning("User token not found for refresh token.")
        raise HTTPException(status_code=400, detail="Invalid Request.")

    await expire_delete(user_token, session)
    logger.info(f"User token expired and deleted for user: {user_token.owner_id}")

    return await _generate_tokens(user_token.user, session)


async def _generate_tokens(user: User, session) -> dict:
    refresh_key = unique_string(100)
    access_key = unique_string(50)

    user_token = UserToken(
        owner_id=user.id,
        refresh_key=refresh_key,
        access_key=access_key,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )

    await save(user_token, session)
    logger.debug(f"User token saved for user: {user.id}")

    access_token = _create_access_token(user, access_key, user_token)
    refresh_token = _create_refresh_token(user, refresh_key, access_key)

    logger.info(f"Tokens generated for user: {user.id}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


async def get_token_user(token: str, session):
    logger.debug("Decoding token to fetch user.")
    payload = get_token_payload(token, settings.JWT_SECRET, settings.JWT_ALGORITHM)

    if payload:
        user_token_id = str_decode(payload.get('ut_ID'))
        user_id = str_decode(payload.get('sub'))
        access_key = payload.get('a_key')

        # Use async select
        result = await session.execute(
            select(UserToken)
            .options(joinedload(UserToken.user))
            .where(
                UserToken.access_key == access_key,
                UserToken.id == user_token_id,
                UserToken.owner_id == user_id,
                UserToken.expires_at > datetime.utcnow()
            )
        )
        user_token = result.scalars().first()  # Get the first result

        if user_token:
            logger.debug(f"User found for token: {user_token.id}")
            return user_token.user

    logger.warning("No valid user found for provided token.")
    return None


async def _verify_user_token(user: User, token: str, email_context: str):
    logger.debug(f"Verifying token for user: {user.id} with context: {email_context}")
    user_token = user.get_context_string(context=email_context)

    token_valid = verify_password(user_token, token)
    if not token_valid:
        logger.warning("Token verification failed for user: {user.id}")
        raise HTTPException(status_code=404, detail="This link is expired or not valid!")

    logger.info(f"Token verified successfully for user: {user.id}")
    
    