from fastapi import HTTPException
from datetime import datetime
import logging
import httpx

from app.db.models import User
from app.core import settings_env,verify_password, verify_password
from app.db.repositories import save_user, get_user_by_email
from .user import fetch_user_info, _get_user,_validate_user_status
from .token import _generate_tokens


logger = logging.getLogger(__name__)
settings = settings_env

async def get_auth_callback(code: str, provider: str, session):
    logger.info(f"Авторизация через {provider} с кодом: {code}")
    
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
        logger.error(f"Не удалось получить токен доступа от {provider}")
        return {"error": "Failed to retrieve access token."}
    
    logger.info(f"Токен доступа получен для {provider}")
    
    name, email = await fetch_user_info(provider, token)
    user =get_user_by_email(email, session)
    
    if not user:
        user = User(
            name=name,
            email=email,
            is_active=True,
            verified_at=datetime.utcnow()
        )
        save_user(user, session)
        logger.info(f"Создан новый пользователь через {provider}: {email}")
    
    return _generate_tokens(user, session)

async def get_login_token(data, session):
    logger.info(f"Попытка входа для пользователя с email: {data.email}")
    
    user = await _get_user(data.email, session)

    if not verify_password(data.password, user.password):
        logger.warning(f"Неудачная попытка входа: неверный пароль для пользователя {data.email}")
        raise HTTPException(status_code=400, detail="Incorrect email or password.")
    
    _validate_user_status(user)
    logger.info(f"Пользователь {data.email} успешно вошел в систему")

    return _generate_tokens(user, session)
