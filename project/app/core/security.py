from passlib.context import CryptContext
from datetime import datetime,timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException
import logging
import jwt
import base64

from app.db.models.user import UserToken
from app.core.config import settings_env
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
settings= settings_env
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def str_encode(string: str) -> str:
    if string is None:
        raise ValueError("Input string cannot be None")
    return base64.b85encode(string.encode('ascii')).decode('ascii')

def str_decode(string: str) -> str:
    if string is None:
        raise ValueError("Input string cannot be None")
    return base64.b85decode(string.encode('ascii')).decode('ascii')


def verify_token(user_token, token):
    try:
        return verify_password(user_token, token)
    except Exception as e:
        logging.exception(e)
        return False


def generate_token(payload: dict, secret: str, algo: str, expiry: timedelta):
    expire = datetime.utcnow() + expiry
    payload.update({"exp": expire})
    return jwt.encode(payload, secret, algorithm=algo)


def get_token_payload(token: str, secret: str, algo: str):
    try:
        payload = jwt.decode(token, secret, algorithms=algo)
    except Exception as jwt_exec:
        logging.debug(f"JWT Error: {str(jwt_exec)}")
        payload = None
    return payload



async def get_token_user(token: str, db):
    payload = get_token_payload(token, settings.JWT_SECRET, settings.JWT_ALGORITHM)
    if payload:
        user_token_id = str_decode(payload.get('rt_ID'))
        user_id = str_decode(payload.get('sub'))
        access_key = payload.get('a_key')
        user_token = db.query(UserToken).options(joinedload(UserToken.user)).filter(
            UserToken.access_key == access_key,
            UserToken.id == user_token_id,
            UserToken.owner_id == user_id,
            UserToken.expires_at > datetime.utcnow()
            ).first()
        if user_token:
            return user_token.user
    return None

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = await get_token_user(token=token, db=db)
    print(f"USER::::{user}::::")
    if user:
        return user
    raise HTTPException(status_code=401, detail="Not authorised.")





    