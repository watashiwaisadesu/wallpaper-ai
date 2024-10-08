from authlib.integrations.starlette_client import OAuthError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer,OAuth2AuthorizationCodeBearer,SecurityScopes
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime, timedelta
import logging
import httpx

from app.models.user import User, UserToken
from app.config import security
from app.config.settings import settings_env
from app.auth.services import email
from app.utils import email_context, string
from app.repositories import user_repository


settings = settings_env

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

    await _verify_user_token(user, data.token, email_context.USER_VERIFY_ACCOUNT)

    user.is_active = True
    user.verified_at = datetime.utcnow()
    user_repository.save_user(user, session)
    await email.send_account_activation_confirmation_email(user, background_tasks=background_tasks)
    return user

async def get_auth_callback(code: str, provider: str, session):
    if provider == "github":
        token_url = "https://github.com/login/oauth/access_token"
    elif provider == "google":
        token_url = "https://oauth2.googleapis.com/token"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID if provider == "github" else settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET if provider == "github" else settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }    
    if provider == "google":
        params["redirect_uri"] = settings.GOOGLE_REDIRECT_URI
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url=token_url, params=params, headers=headers)
        response_json = response.json()
        token = response_json.get('access_token')
    if not token:
        return {"error": "Failed to retrieve access token."}
    name, email = await fetch_user_info(provider, token)
    user = user_repository.get_user_by_email(email,session)
    if not user:
        user = User(
            name=name,
            email=email,
            is_active=True
            ) 
        user_repository.save_user(user, session)  
    return _generate_tokens(user,session)
    
     
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
    

async def reset_user_password(data, session):
    user = await _get_user(data.email, session)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    _validate_user_status(user)

    # Verify the user's reset password token
    await _verify_user_token(user, data.token, email_context.FORGOT_PASSWORD)

    # Update the user's password
    user.password = security.hash_password(data.password)
    user_repository.save_user(user, session)

async def fetch_user_info(provider: str, token: str):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        if provider == "github":
            response = await client.get("https://api.github.com/user", headers=headers)
            data = response.json()
            print(f"DATA JSON PROVIDER::  {data} ::")
            username = data['login']  # GitHub returns 'login'
            email = data.get('email')  # GitHub may not return email directly
            return username, email
        elif provider == "google":
            response = await client.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
            data = response.json()
            name = data.get('name')  # Google returns 'name'
            email = data['email']
            return name, email
    return None, None

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


async def _verify_user_token(user: User, token: str, email_context: str):
    user_token = user.get_context_string(context=email_context)

    # Verify the token
    token_valid = security.verify_password(user_token, token)
    if not token_valid:
        raise HTTPException(status_code=404, detail="This link is expired or not valid!")
    
    
def _validate_user_status(user: User):
    if not user.verified_at:
        raise HTTPException(status_code=400, detail="User is not verified.")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active.")

    
