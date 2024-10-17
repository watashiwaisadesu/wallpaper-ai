from fastapi import HTTPException
from datetime import datetime
import logging
import httpx

from app.db.models import User
from app.core import settings_env, verify_password
from app.db.repositories import save, get_user_by_email
from .user import oauth_fetch_user, _get_user,_validate_user_status
from .token import _generate_tokens


logger = logging.getLogger(__name__)
settings = settings_env


async def get_auth_callback(code: str, session):
    token_url = "https://accounts.google.com/o/oauth2/token"
    params = {
        "client_id": settings_env.GOOGLE_CLIENT_ID,
        "client_secret": settings_env.GOOGLE_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings_env.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    headers = {"Accept": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            logger.debug("Requesting access token from Google OAuth.")
            response = await client.post(token_url, params=params, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses
            access_token = response.json()
            token = access_token['access_token']
            logger.info("Access token received successfully.")

        # Fetch user information
        async with httpx.AsyncClient() as client:
            headers.update({'Authorization': f"Bearer {token}"})
            logger.debug("Fetching user information from Google.")
            name, email = await oauth_fetch_user(token)
            logger.info(f"User information fetched: {name} ({email})")

        # Load or create user
        user = await get_user_by_email(email, session)
        if not user:
            logger.info(f"Creating new user: {email}")
            user = User(
                name=name,
                email=email,
                is_active=True,
                verified_at=datetime.utcnow()
            )
        else:
            logger.info(f"User already exists: {email}")

        await save(user, session)
        logger.debug(f"User {email} saved to the database.")

        return await _generate_tokens(user, session)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Failed to get access token.")

    except Exception as e:
        logger.exception("An unexpected error occurred while processing OAuth callback.")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_login_token(data, session):
    logger.debug(f"Attempting to log in user: {data.email}")
    user = await _get_user(data.email, session)

    if not verify_password(data.password, user.password):
        logger.warning(f"Failed login attempt for user: {data.email}. Incorrect password.")
        raise HTTPException(status_code=400, detail="Incorrect email or password.")

    _validate_user_status(user)
    logger.info(f"User {data.email} logged in successfully.")

    return await _generate_tokens(user, session)
