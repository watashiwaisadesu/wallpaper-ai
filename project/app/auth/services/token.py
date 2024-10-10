from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

from app.db.models import User, UserToken
from app.core import get_token_payload, str_decode, str_encode, generate_token, settings_env, verify_password
from app.auth.services import email
from app.utils import  unique_string
from app.db.repositories import save, get_user_token_by_keys, delete

settings = settings_env


def _create_access_token(user: User, access_key: str, user_token: UserToken) -> str:
    
    at_payload = {
        "sub": str_encode(str(user.id)),
        'a_key': access_key,
        'rt_ID': str_encode(str(user_token.id)),
        'name': str_encode(user.name)
    }

    at_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = generate_token(at_payload, settings.JWT_SECRET, settings.JWT_ALGORITHM, at_expires)
    return token


def _create_refresh_token(user: User, refresh_key: str, access_key: str) -> str:
    
    rt_payload = {
        "sub": str_encode(str(user.id)),
        "r_key": refresh_key,
        'a_key': access_key
    }    
    rt_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    token = generate_token(rt_payload, settings.SECRET_KEY, settings.JWT_ALGORITHM, rt_expires)
    return token


async def get_refresh_token(refresh_token, session):

    token_payload = get_token_payload(refresh_token, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    if not token_payload:
        raise HTTPException(status_code=400, detail="Invalid Request.")
    
    user_token = get_user_token_by_keys(
        refresh_key=token_payload.get('r_key'),
        access_key=token_payload.get('a_key'),
        user_id=str_decode(token_payload.get('sub')),
        session=session
    )
    
    if not user_token:
        raise HTTPException(status_code=400, detail="Invalid Request.")
    
    delete(user_token, session)
    
    return _generate_tokens(user_token.user, session)


def _generate_tokens(user: User, session) -> dict:

    refresh_key = unique_string(100)
    access_key = unique_string(50)
    rt_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    user_token = UserToken(
        owner_id=user.id,
        refresh_key=refresh_key,
        access_key=access_key,
        expires_at=datetime.utcnow() + rt_expires
    )
    
    save(user_token, session)

    access_token = _create_access_token(user, access_key, user_token)
    refresh_token = _create_refresh_token(user, refresh_key, access_key)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


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


async def _verify_user_token(user: User, token: str, email_context: str):
    
    user_token = user.get_context_string(context=email_context)

    # Проверка токена
    token_valid = verify_password(user_token, token)
    if not token_valid:
        raise HTTPException(status_code=404, detail="This link is expired or not valid!")
    
    