from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException
import logging
import jwt
import base64

from app.db.models.user import UserToken
from app.core.config import settings_env
from app.core.database import get_db

# Initialize logger
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
settings = settings_env
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    logger.debug(f"Hashing password.")
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    logger.debug(f"Verifying password.")
    return pwd_context.verify(plain_password, hashed_password)


def str_encode(string: str) -> str:
    if string is None:
        raise ValueError("Input string cannot be None")
    logger.debug(f"Encoding string: {string}")
    return base64.b85encode(string.encode('ascii')).decode('ascii')


def str_decode(string: str) -> str:
    if string is None:
        raise ValueError("Input string cannot be None")
    logger.debug(f"Decoding string: {string}")
    return base64.b85decode(string.encode('ascii')).decode('ascii')


def verify_token(user_token, token):
    logger.debug("Verifying token.")
    try:
        return verify_password(user_token, token)
    except Exception as e:
        logger.exception("Token verification failed.")
        return False


def generate_token(payload: dict, secret: str, algo: str, expiry: timedelta):
    logger.debug("Generating JWT token.")
    expire = datetime.utcnow() + expiry
    payload.update({"exp": expire})
    return jwt.encode(payload, secret, algorithm=algo)


def get_token_payload(token: str, secret: str, algo: str):
    logger.debug("Decoding JWT token payload.")
    try:
        payload = jwt.decode(token, secret, algorithms=algo)
    except Exception as jwt_exec:
        logger.debug(f"JWT Error: {str(jwt_exec)}")
        payload = None
    return payload


async def get_token_user(token: str, db):
    logger.debug(f"Getting user from token: {token}")
    payload = get_token_payload(token, settings.JWT_SECRET, settings.JWT_ALGORITHM)
    if payload:
        user_token_id = str_decode(payload.get('rt_ID'))
        user_id = str_decode(payload.get('sub'))
        access_key = payload.get('a_key')
        logger.debug(f"Decoded payload: user_token_id={user_token_id}, user_id={user_id}")
        user_token = db.query(UserToken).options(joinedload(UserToken.user)).filter(
            UserToken.access_key == access_key,
            UserToken.id == user_token_id,
            UserToken.owner_id == user_id,
            UserToken.expires_at > datetime.utcnow()
        ).first()
        if user_token:
            logger.debug(f"User token found for user ID: {user_token.user.id}")
            return user_token.user
        logger.debug("No valid user token found.")
    return None


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.debug("Fetching current user.")
    user = await get_token_user(token=token, db=db)
    if user:
        logger.debug(f"User found: {user.email}")
        return user
    logger.debug("User not authorized.")
    raise HTTPException(status_code=401, detail="Not authorized.")
