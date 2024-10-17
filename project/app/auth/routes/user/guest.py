from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, BackgroundTasks, Depends, status, Header, HTTPException
import logging

from app.core import get_db
from app.responses import LoginResponse
from app.schemas import LoginRequest, EmailRequest, ResetRequest
from app.auth.services import get_login_token, get_refresh_token, forgot_password_email_link, reset_user_password

guest_router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

logger = logging.getLogger(__name__)


@guest_router.post("/login", status_code=200, response_model=LoginResponse)
async def user_login(data: LoginRequest, session: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Попытка входа пользователя с email: {data.email}")
        token = await get_login_token(data, session)
        logger.info(f"Пользователь с email {data.email} успешно вошел в систему.")
        return token
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={e}
        )


# Обновление токена
@guest_router.post("/refresh", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def refresh_token(refresh_token: str = Header(...), session: AsyncSession = Depends(get_db)):
    try:
        logger.info("Обновление токена.")
        new_token = await get_refresh_token(refresh_token, session)
        logger.info("Токен успешно обновлен.")
        return new_token
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={e}
        )


# Сброс пароля
@guest_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: EmailRequest, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Запрос на сброс пароля для email: {data.email}")
        await forgot_password_email_link(data, background_tasks, session)
        logger.info(f"Ссылка для сброса пароля отправлена на email: {data.email}")
        return {"message": "An email with a password reset link has been sent to you."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={e}
        )


# Обновление пароля
@guest_router.put("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetRequest, session: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Обновление пароля для пользователя с email: {data.email}")
        await reset_user_password(data, session)
        logger.info(f"Пароль для пользователя с email {data.email} успешно обновлен.")
        return {"message": "Your password has been updated."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={e}
        )


