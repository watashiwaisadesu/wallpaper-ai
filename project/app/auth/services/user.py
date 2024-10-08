from fastapi import HTTPException, BackgroundTasks
from datetime import datetime, timedelta
import logging
import httpx

from app.db.models.user import User, UserToken
from app.core import security
from app.core.config import settings_env
from app.auth.services import email
from app.utils import email_context, string
from app.db.repositories import user_repository


settings = settings_env

# Инициализация логгера
logger = logging.getLogger(__name__)

async def create_user_account(data, background_tasks: BackgroundTasks, session):
    logger.info(f"Создание учетной записи для пользователя с email: {data.email}")
    
    user_exist = await user_repository.load_user(data.email, session)
    if user_exist:
        logger.warning(f"Попытка создать учетную запись с уже существующим email: {data.email}")
        raise HTTPException(status_code=400, detail="Email already exists.")

    user = User(
        name=data.name,
        email=data.email,
        password=security.hash_password(data.password),
        is_active=False
    )
    
    user_repository.save_user(user, session)
    logger.info(f"Учетная запись создана для пользователя с email: {data.email}, отправка письма для подтверждения")
    
    await email.send_account_verification_email(user, background_tasks=background_tasks)
    logger.info(f"Письмо для подтверждения учетной записи отправлено на email: {data.email}")
    return user

async def activate_user_account(data, background_tasks: BackgroundTasks, session):
    logger.info(f"Активация учетной записи пользователя с email: {data.email}")
    
    user = await user_repository.load_user(data.email, session)
    if not user:
        logger.error(f"Пользователь с email {data.email} не найден.")
        raise HTTPException(status_code=404, detail="User not found.")

    await _verify_user_token(user, data.token, email_context.USER_VERIFY_ACCOUNT)

    user.is_active = True
    user.verified_at = datetime.utcnow()
    user_repository.save_user(user, session)
    
    logger.info(f"Учетная запись пользователя с email: {data.email} активирована.")
    await email.send_account_activation_confirmation_email(user, background_tasks=background_tasks)
    return user

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
    user = user_repository.get_user_by_email(email, session)
    
    if not user:
        user = User(
            name=name,
            email=email,
            is_active=True
        )
        user_repository.save_user(user, session)
        logger.info(f"Создан новый пользователь через {provider}: {email}")
    
    return _generate_tokens(user, session)

async def get_login_token(data, session):
    logger.info(f"Попытка входа для пользователя с email: {data.email}")
    
    user = await _get_user(data.email, session)

    if not security.verify_password(data.password, user.password):
        logger.warning(f"Неудачная попытка входа: неверный пароль для пользователя {data.email}")
        raise HTTPException(status_code=400, detail="Incorrect email or password.")
    
    _validate_user_status(user)
    logger.info(f"Пользователь {data.email} успешно вошел в систему")

    return _generate_tokens(user, session)

async def get_refresh_token(refresh_token, session):
    logger.info(f"Обновление токена для пользователя с refresh_token: {refresh_token[:10]}...")

    token_payload = security.get_token_payload(refresh_token, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    if not token_payload:
        logger.error("Невалидный запрос на обновление токена")
        raise HTTPException(status_code=400, detail="Invalid Request.")
    
    user_token = user_repository.get_user_token_by_keys(
        refresh_key=token_payload.get('r_key'),
        access_key=token_payload.get('a_key'),
        user_id=security.str_decode(token_payload.get('sub')),
        session=session
    )
    
    if not user_token:
        logger.error("Невалидный запрос на обновление токена, токен не найден")
        raise HTTPException(status_code=400, detail="Invalid Request.")
    
    user_repository.save_user(user_token, session)
    logger.info(f"Токен пользователя обновлен для пользователя с ID: {user_token.owner_id}")

    return _generate_tokens(user_token.user, session)
def _generate_tokens(user: User, session) -> dict:
    logger.info(f"Генерация токенов для пользователя с ID: {user.id}")

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
    logger.info(f"Токены сгенерированы для пользователя с ID: {user.id}")

    access_token = _create_access_token(user, access_key, user_token)
    refresh_token = _create_refresh_token(user, refresh_key, access_key)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

async def email_forgot_password_link(data, background_tasks, session):
    logger.info(f"Запрос на сброс пароля для пользователя с email: {data.email}")

    user = await _get_user(data.email, session)

    _validate_user_status(user)
    
    await email.send_password_reset_email(user, background_tasks)
    logger.info(f"Ссылка для сброса пароля отправлена на email: {data.email}")

async def reset_user_password(data, session):
    logger.info(f"Сброс пароля для пользователя с email: {data.email}")
    
    user = await _get_user(data.email, session)
    
    if not user:
        logger.error(f"Сброс пароля не удался: пользователь с email {data.email} не найден.")
        raise HTTPException(status_code=400, detail="Invalid request")
    
    _validate_user_status(user)

    # Проверка токена сброса пароля
    await _verify_user_token(user, data.token, email_context.FORGOT_PASSWORD)

    # Обновление пароля пользователя
    user.password = security.hash_password(data.password)
    user_repository.save_user(user, session)
    logger.info(f"Пароль успешно сброшен для пользователя с email: {data.email}")

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
    return None, None

async def _get_user(email: str, session) -> User:
    logger.info(f"Поиск пользователя с email: {email}")
    user = await user_repository.load_user(email, session)
    
    if not user:
        logger.warning(f"Пользователь не найден: {email}")
        raise HTTPException(status_code=404, detail=f"User not found: {email}")
    
    logger.info(f"Пользователь найден: {email}")
    return user

def _create_access_token(user: User, access_key: str, user_token: UserToken) -> str:
    logger.info(f"Создание access токена для пользователя с ID: {user.id}")
    
    at_payload = {
        "sub": security.str_encode(str(user.id)),
        'a_key': access_key,
        'rt_ID': security.str_encode(str(user_token.id)),
        'name': security.str_encode(user.name)
    }

    at_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.generate_token(at_payload, settings.JWT_SECRET, settings.JWT_ALGORITHM, at_expires)
    logger.info(f"Access токен создан для пользователя с ID: {user.id}")
    return token

def _create_refresh_token(user: User, refresh_key: str, access_key: str) -> str:
    logger.info(f"Создание refresh токена для пользователя с ID: {user.id}")
    
    rt_payload = {
        "sub": security.str_encode(str(user.id)),
        "r_key": refresh_key,
        'a_key': access_key
    }    
    rt_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    token = security.generate_token(rt_payload, settings.SECRET_KEY, settings.JWT_ALGORITHM, rt_expires)
    logger.info(f"Refresh токен создан для пользователя с ID: {user.id}")
    return token

async def _verify_user_token(user: User, token: str, email_context: str):
    logger.info(f"Проверка токена для пользователя с ID: {user.id}")
    
    user_token = user.get_context_string(context=email_context)

    # Проверка токена
    token_valid = security.verify_password(user_token, token)
    if not token_valid:
        logger.warning("Токен недействителен или истек.")
        raise HTTPException(status_code=404, detail="This link is expired or not valid!")
    
    logger.info(f"Токен успешно проверен для пользователя с ID: {user.id}")

def _validate_user_status(user: User):
    logger.info(f"Валидация статуса пользователя с ID: {user.id}")
    
    if not user.verified_at:
        logger.warning("Пользователь не подтвержден.")
        raise HTTPException(status_code=400, detail="User is not verified.")
    
    if not user.is_active:
        logger.warning("Пользователь не активен.")
        raise HTTPException(status_code=400, detail="User is not active.")
    
    logger.info(f"Статус пользователя с ID: {user.id} валиден.")
