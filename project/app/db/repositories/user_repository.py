from datetime import datetime
from sqlalchemy.orm import joinedload, Session
import logging

from app.db.models import User, UserToken

# Initialize logger
logger = logging.getLogger(__name__)


def get_user_by_email(email: str, session):
    logger.debug(f"Fetching user by email: {email}")
    return session.query(User).filter_by(email=email).first()


def save_user(user, session: Session):
    logger.debug(f"Saving user or userToken")
    try:
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.debug(f"User saved successfully.")
    except Exception as save_exc:
        session.rollback()
        logger.error(f"Failed to save user, Error: {str(save_exc)}")
        raise save_exc


def get_user_token_by_keys(refresh_key, access_key, user_id, session):
    logger.debug(f"Fetching user token by keys for user ID: {user_id}")
    return session.query(UserToken).options(joinedload(UserToken.user)).filter(
        UserToken.refresh_key == refresh_key,
        UserToken.access_key == access_key,
        UserToken.owner_id == user_id,
        UserToken.expires_at > datetime.utcnow()
    ).first()


async def load_user(email: str, db):
    logger.debug(f"Loading user by email: {email}")
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            logger.debug(f"User found: {user.email}")
        else:
            logger.debug(f"No user found for email: {email}")
    except Exception as user_exec:
        logger.error(f"Error loading user by email: {email}, Error: {str(user_exec)}")
        user = None
    return user
