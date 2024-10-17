from fastapi import HTTPException
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from app.db.models import User, UserToken

# Initialize logger
logger = logging.getLogger(__name__)


async def get_user_by_email(email: str, session: AsyncSession):
    logger.debug(f"Fetching user by email: {email}")
    try:
        result = await session.execute(
            select(User).filter_by(email=email)
        )
        user = result.scalars().first()  # Get the first result
        return user
    except Exception as e:
        logger.error(f"Error fetching user by email: {email}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user by email.")


async def load_user(email: str, session: AsyncSession):
    user = await get_user_by_email(email, session)
    return user


async def get_user_token_by_user_id(user_id: str, session: AsyncSession):
    try:
        result = await session.execute(
            select(UserToken).filter(UserToken.owner_id == user_id)
        )
        token = result.scalars().first()  # Get the first result
        return token
    except Exception as e:
        logger.error(f"Error fetching user token by user_id: {user_id}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user token.")


async def save(model, session: AsyncSession):
    try:
        session.add(model)
        await session.commit()
        await session.refresh(model)
        logger.debug(f"Saved successfully: {model}")
    except Exception as save_exc:
        await session.rollback()
        logger.error(f"Failed to save model: {model}, Error: {str(save_exc)}")
        raise HTTPException(status_code=500, detail="Failed to save model.")


async def expire_delete(model, session: AsyncSession):
    try:
        model.expires_at = datetime.utcnow()
        logger.debug(f"Model expired at: {model.expires_at}")
        await session.commit()  # Commit before deletion to update the expires_at field
        await session.delete(model)  # Use await for delete
        await session.commit()  # Commit after deletion
        logger.debug(f"Deleted model: {model}")
    except Exception as e:
        await session.rollback()  # Rollback in case of error
        logger.error(f"Failed to expire and delete model: {model}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to expire and delete.")


async def logout_user(user, session: AsyncSession):
    try:
        result = await session.execute(
            select(UserToken).filter(UserToken.owner_id == user.id)
        )
        tokens = result.scalars().all()
        if not tokens:
            logger.debug(f"No tokens found for user: {user.id}")
            return {"detail": "No active sessions found."}

        for token in tokens:
            await expire_delete(token, session)

        return {"detail": "Logged out successfully."}
    except Exception as e:
        logger.error(f"Failed to logout user: {user.id}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to logout user.")
