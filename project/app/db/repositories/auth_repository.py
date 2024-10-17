from fastapi import HTTPException
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.models import UserToken
import logging

logger = logging.getLogger(__name__)

async def get_user_token_by_keys(refresh_key: str, access_key: str, user_id: str, session: AsyncSession):
    try:
        result = await session.execute(
            select(UserToken)
            .options(selectinload(UserToken.user))  # Use selectinload for async
            .filter(
                UserToken.refresh_key == refresh_key,
                UserToken.access_key == access_key,
                UserToken.owner_id == user_id,
                UserToken.expires_at > datetime.utcnow()
            )
        )
        user_token = result.scalars().first()  # Get the first result

        if user_token:
            logger.info(f"Successfully fetched user token for user ID: {user_id}")
        else:
            logger.warning(f"No user token found for user ID: {user_id}")

        return user_token

    except Exception as e:
        logger.error(f"Error fetching user token for user ID: {user_id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching user token.")
