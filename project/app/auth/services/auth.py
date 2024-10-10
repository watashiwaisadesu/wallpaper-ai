from fastapi import HTTPException
from datetime import datetime
import logging
import httpx

from app.db.models import User
from app.core import settings_env, verify_password
from app.db.repositories import save, get_user_by_email, delete, get_user_token_by_user_id
from .user import fetch_user_info, _get_user,_validate_user_status
from .token import _generate_tokens


logger = logging.getLogger(__name__)
settings = settings_env

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
        raise HTTPException(status_code=400,detail="Failed to retrieve access token.")
    
    
    name, email = await fetch_user_info(provider, token)
    user =get_user_by_email(email, session)
    
    if not user:
        user = User(
            name=name,
            email=email,
            is_active=True,
            verified_at=datetime.utcnow()
        )
        save(user, session)
    
    return _generate_tokens(user, session)

async def get_login_token(data, session):
    user = await _get_user(data.email, session)

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password.")

    # user_token = get_user_token_by_user_id(user.id, session)
    #
    # if user_token:
    #     delete(user_token, session)

    _validate_user_status(user)

    return _generate_tokens(user, session)
