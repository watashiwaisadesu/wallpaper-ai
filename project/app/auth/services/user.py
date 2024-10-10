from fastapi import HTTPException, BackgroundTasks,  Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from sqlalchemy.orm import Session
import httpx

from app.db.models import User
from app.core import settings_env, hash_password, get_db, validate
from app.auth.services import email
from app.utils import USER_VERIFY_ACCOUNT, FORGOT_PASSWORD
from app.db.repositories import load_user,save
from .token import _verify_user_token, get_token_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
settings = settings_env


async def create_user_account_service(data, background_tasks: BackgroundTasks, session):
    try:
        user_exist = await load_user(data.email, session)
        if user_exist:
            raise HTTPException(status_code=400, detail="Email already exists.")

        # Uncomment the password validation if necessary
        if not validate(data.password):
            raise HTTPException(status_code=400, detail="Please create valid password!")

        user = User(
            name=data.name,
            email=data.email,
            password=hash_password(data.password),
            is_active=False
        )

        save(user, session)  # Ensure this is an awaitable if it's async
        
        await email.send_account_verification_email(user, background_tasks=background_tasks)
        
        return user
    except HTTPException as http_ex:
        raise http_ex  # Reraise to propagate the HTTP error

    except Exception as ex:
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def activate_user_account(data, background_tasks: BackgroundTasks, session):
    
    user = await load_user(data.email, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await _verify_user_token(user, data.token, USER_VERIFY_ACCOUNT)

    user.is_active = True
    user.verified_at = datetime.utcnow()
    save(user, session)

    await email.send_account_activation_confirmation_email(user, background_tasks=background_tasks)
    return user

async def email_forgot_password_link(data, background_tasks, session):

    user = await _get_user(data.email, session)
    if not user.password:  # Проверка только на None или пустую строку
        raise ValueError("OAuth users cannot reset their password")

    _validate_user_status(user)
    
    await email.send_password_reset_email(user, background_tasks)

async def reset_user_password(data, session):
    
    user = await _get_user(data.email, session)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")
    if not user.password:  # Проверка только на None или пустую строку
        raise ValueError("OAuth users cannot reset their password")
    
    _validate_user_status(user)

    # Проверка токена сброса пароля
    await _verify_user_token(user, data.token, FORGOT_PASSWORD)

    # Обновление пароля пользователя
    if not validate(data.password):
        raise HTTPException(status_code=400, detail="Please create valid password!")
    user.password = hash_password(data.password)
    save(user, session)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = await get_token_user(token=token, db=db)
    if user:
        return user
    raise HTTPException(status_code=401, detail="Not authorized.")

async def fetch_user_info(provider: str, token: str):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        if provider == "github":
            response = await client.get("https://api.github.com/user", headers=headers)
            data = response.json()
            username = data['login']  # GitHub возвращает 'login'
            email = data.get('email')  # GitHub может не возвращать email напрямую
            return username, email
        elif provider == "google":
            response = await client.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
            data = response.json()
            name = data.get('name')  # Google возвращает 'name'
            email = data['email']
            return name, email

    raise HTTPException(status_code=401, detail="Не удалось извлечь информацию о пользователе.")

async def _get_user(email: str, session) -> User:
    user = await load_user(email, session)
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {email}")

    return user

def _validate_user_status(user: User):
    
    if not user.verified_at:
        raise HTTPException(status_code=400, detail="User is not verified.")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active.")
    

