from authlib.integrations.starlette_client import OAuthError
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime, timedelta
import logging

from app.models.user import User, UserToken
from app.config import security, settings, oauth
from app.services import email
from app.utils import email_context, string
from app.repositories import user_repository



settings = settings.get_settings()


async def create_user_account(data, background_tasks: BackgroundTasks, session):
    user_exist = await user_repository.load_user(email, session)
    if user_exist:
        raise HTTPException(status_code=400, detail="Email already exists.")

    user = User(
        name=data.name,
        email=data.email,
        password=security.hash_password(data.password),
        is_active=False
    )
    
    user_repository.save_user(user, session)
    await email.send_account_verification_email(user, background_tasks=background_tasks)
    return user


async def activate_user_account(data, background_tasks: BackgroundTasks, session):
    user = await user_repository.load_user(data.email, session)

    _verify_user_token(user, data.token)
    user.is_active = True
    user.verified_at = datetime.utcnow()
    user_repository.save_user(user, session)
    await email.send_account_activation_confirmation_email(user, background_tasks=background_tasks)
    return user


async def get_oauth_login_token(oauth_data, session):
    try:
        access_token = await oauth.oauth.google.authorize_access_token(oauth_data['request'])
        user_data = await oauth.oauth.google.parse_id_token(oauth_data['request'], access_token)

        email = user_data['email']
        name = user_data['name']

        # Check if the user exists in the database
        user = await _get_user(email, session)
        
        if not user:
            # Create a new user if they don't exist
            user = User(email=email, name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        # Generate tokens for the user
        return _generate_tokens(user, session)

    except OAuthError:
        raise HTTPException(status_code=401, detail="OAuth error occurred.")

    
    
  
async def get_login_token(data, session):
    user = await _get_user(data.email, session)

    if not security.verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password.")
    
    _validate_user_status(user)

    return _generate_tokens(user, session)


async def get_refresh_token(refresh_token,session):
    token_payload = security.get_token_payload(refresh_token, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    if not token_payload:
        raise HTTPException(status_code=400, detail="Invalid Request.")
    
    user_token = user_repository.get_user_token_by_keys(
        refresh_key=token_payload.get('r_key'),
        access_key=token_payload.get('a_key'),
        user_id=security.str_decode(token_payload.get('sub')),
        session=session
    )
    if not user_token:
        raise HTTPException(status_code=400, detail="Invalid Request.")
    
    user_repository.save_user(user_token, session)
    return _generate_tokens(user_token.user, session)
    

def _generate_tokens(user: User, session) -> dict:
    refresh_key = string.unique_string(100)
    access_key = string.unique_string(50)
    rt_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    user_token = UserToken(
        owner_id=user.id,
        refresh_key=refresh_key,
        access_key=access_key,
        expires_at=datetime.utcnow() + rt_expires
    )
    
    user_repository.save_user(user_token, session)

    access_token = _create_access_token(user, access_key, user_token)
    refresh_token = _create_refresh_token(user, refresh_key, access_key)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


    
     
async def email_forgot_password_link(data, background_tasks, session):
    user = await _get_user(data.email, session)
    
    _validate_user_status(user)
    
    await email.send_password_reset_email(user, background_tasks)
    
    
async def reset_user_password(data,session):
    user = await _get_user(data.email, session)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if not user.verified_at:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    user_token = user.get_context_string(context=email_context.FORGOT_PASSWORD)
    try:
        token_valid = security.verify_password(user_token, data.token)
    except Exception as verify_exec:
        logging.exception(verify_exec)
        token_valid = False
    if not token_valid:
        raise HTTPException(status_code=400, detail="Token is not valid.")
    user.password = security.hash_password(data.password)
    user_repository.save_user(user,session)


async def _get_user(email: str, session) -> User:
    user = await user_repository.load_user(email, session)
    if not user:
        logging.warning(f"User not found: {email}")
        raise HTTPException(status_code=404, detail="This link is not valid")
    return user
 
    
def _create_access_token(user: User, access_key: str, user_token: UserToken) -> str:
    at_payload = {
        "sub": security.str_encode(str(user.id)),
        'a_key': access_key,
        'rt_ID': security.str_encode(str(user_token.id)),
        'name': security.str_encode(user.name)
    }

    at_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return security.generate_token(at_payload, settings.JWT_SECRET, settings.JWT_ALGORITHM, at_expires)


def _create_refresh_token(user: User, refresh_key: str, access_key: str) -> str:
    rt_payload = {
        "sub": security.str_encode(str(user.id)),
        "r_key": refresh_key,
        'a_key': access_key
    }    
    rt_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return security.generate_token(rt_payload, settings.SECRET_KEY, settings.JWT_ALGORITHM, rt_expires)


def _verify_user_token(user: User, token: str):
    user_token = user.get_context_string(context=email_context.USER_VERIFY_ACCOUNT)
    if not security.verify_password(user_token, token):
        raise HTTPException(status_code=404, detail="This link is expired or not valid!")
    
    
def _validate_user_status(user: User):
    if not user.verified_at:
        raise HTTPException(status_code=400, detail="User is not verified.")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active.")

    
