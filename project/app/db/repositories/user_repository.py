from fastapi import HTTPException
from datetime import datetime
from sqlalchemy.orm import joinedload, Session
import logging

from app.db.models import User, UserToken

# Initialize logger
logger = logging.getLogger(__name__)


def get_user_by_email(email: str, session):
    logger.debug(f"Fetching user by email: {email}")
    return session.query(User).filter_by(email=email).first()

def get_user_token_by_user_id(user_id, session):
    return session.query(UserToken).filter(UserToken.owner_id == user_id).first()

def save(model, session: Session):
    logger.debug(f"Saving user or userToken")
    try:
        session.add(model)
        session.commit()
        session.refresh(model)
        logger.debug(f"User saved successfully.")
    except Exception as save_exc:
        session.rollback()
        logger.error(f"Failed to save user, Error: {str(save_exc)}")
        raise save_exc
    
def delete(model, session: Session):
    try:
        session.delete(model)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user token.")

async def load_user(email: str, db):
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
