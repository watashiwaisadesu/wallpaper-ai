from fastapi import HTTPException, BackgroundTasks,  Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import httpx

from app.db.models import User
from app.core import settings_env, hash_password, get_db, validate
from app.auth.services import email
from app.utils import USER_VERIFY_ACCOUNT, FORGOT_PASSWORD
from app.db.repositories import load_user,save_user
from .token import _verify_user_token, get_token_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
settings = settings_env

# Инициализация логгера
logger = logging.getLogger(__name__)

async def create_user_account_service(data, background_tasks: BackgroundTasks, session):
    logger.info(f"Создание учетной записи для пользователя с email: {data.email}")
   
    try:
        user_exist = await load_user(data.email, session)
        if user_exist:
            logger.warning(f"Попытка создать учетную запись с уже существующим email: {data.email}")
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

        save_user(user, session)  # Ensure this is an awaitable if it's async

        logger.info(f"Учетная запись создана для пользователя с email: {data.email}, отправка письма для подтверждения")
        
        await email.send_account_verification_email(user, background_tasks=background_tasks)
        logger.info(f"Письмо для подтверждения учетной записи отправлено на email: {data.email}")
        
        return user
    except HTTPException as http_ex:
        logger.error(f"HTTPException occurred: {http_ex.detail}")
        raise http_ex  # Reraise to propagate the HTTP error

    except Exception as ex:
        logger.error(f"Unexpected error occurred: {str(ex)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def activate_user_account(data, background_tasks: BackgroundTasks, session):
    logger.info(f"Активация учетной записи пользователя с email: {data.email}")
    
    user = await load_user(data.email, session)
    if not user:
        logger.error(f"Пользователь с email {data.email} не найден.")
        raise HTTPException(status_code=404, detail="User not found.")

    await _verify_user_token(user, data.token, USER_VERIFY_ACCOUNT)

    user.is_active = True
    user.verified_at = datetime.utcnow()
    save_user(user, session)
    
    logger.info(f"Учетная запись пользователя с email: {data.email} активирована.")
    await email.send_account_activation_confirmation_email(user, background_tasks=background_tasks)
    return user

async def email_forgot_password_link(data, background_tasks, session):

    logger.info(f"Запрос на сброс пароля для пользователя с email: {data.email}")

    user = await _get_user(data.email, session)
    if user.password == "" or "null":
        raise ValueError("OAuth users cannot reset their password")

    _validate_user_status(user)
    
    await email.send_password_reset_email(user, background_tasks)
    logger.info(f"Ссылка для сброса пароля отправлена на email: {data.email}")

async def reset_user_password(data, session):
    logger.info(f"Сброс пароля для пользователя с email: {data.email}")
    
    user = await _get_user(data.email, session)
    
    if not user:
        logger.error(f"Сброс пароля не удался: пользователь с email {data.email} не найден.")
        raise HTTPException(status_code=400, detail="Invalid request")
    if user.password == "" or "null":
        raise ValueError("OAuth users cannot reset their password")
    
    _validate_user_status(user)

    # Проверка токена сброса пароля
    await _verify_user_token(user, data.token, FORGOT_PASSWORD)

    # Обновление пароля пользователя
    user.password = hash_password(data.password)
    save_user(user, session)
    logger.info(f"Пароль успешно сброшен для пользователя с email: {data.email}")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.debug("Fetching current user.")
    user = await get_token_user(token=token, db=db)
    if user:
        logger.debug(f"User found: {user.email}")
        return user
    logger.debug("User not authorized.")
    raise HTTPException(status_code=401, detail="Not authorized.")

async def fetch_user_info(provider: str, token: str):
    logger.info(f"Извлечение информации о пользователе из {provider}")

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        if provider == "github":
            response = await client.get("https://api.github.com/user", headers=headers)
            data = response.json()
            logger.debug(f"Полученные данные от GitHub: {data}")
            username = data['login']  # GitHub возвращает 'login'
            email = data.get('email')  # GitHub может не возвращать email напрямую
            return username, email
        elif provider == "google":
            response = await client.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
            data = response.json()
            logger.debug(f"Полученные данные от Google: {data}")
            name = data.get('name')  # Google возвращает 'name'
            email = data['email']
            return name, email

    logger.warning("Не удалось извлечь информацию о пользователе.")
    raise HTTPException(status_code=401, detail="Не удалось извлечь информацию о пользователе.")

async def _get_user(email: str, session) -> User:
    logger.info(f"Поиск пользователя с email: {email}")
    user = await load_user(email, session)
    
    if not user:
        logger.warning(f"Пользователь не найден: {email}")
        raise HTTPException(status_code=404, detail=f"User not found: {email}")
    
    logger.info(f"Пользователь найден: {email}")
    return user

def _validate_user_status(user: User):
    logger.info(f"Валидация статуса пользователя с ID: {user.id}")
    
    if not user.verified_at:
        logger.warning("Пользователь не подтвержден.")
        raise HTTPException(status_code=400, detail="User is not verified.")
    
    if not user.is_active:
        logger.warning("Пользователь не активен.")
        raise HTTPException(status_code=400, detail="User is not active.")
    
    logger.info(f"Статус пользователя с ID: {user.id} валиден.")

