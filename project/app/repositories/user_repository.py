from datetime import datetime
from sqlalchemy.orm import  joinedload
from sqlalchemy.orm import Session
import logging

from app.models.user import User, UserToken


def get_user_by_email(email: str, session):
    return session.query(User).filter_by(email=email).first()


def save_user(user, session: Session):
    session.add(user)
    session.commit()
    session.refresh(user)
    
    
def get_user_token_by_keys(refresh_key, access_key, user_id, session):
    return session.query(UserToken).options(joinedload(UserToken.user)).filter(
        UserToken.refresh_key == refresh_key,
        UserToken.access_key == access_key,
        UserToken.owner_id == user_id,
        UserToken.expires_at > datetime.utcnow()
    ).first()


async def load_user(email: str, db):
    try:
        user = db.query(User).filter(User.email == email).first()
    except Exception as user_exec:
        logging.info(f"User Not Found, Email: {email}")
        user = None
    return user



