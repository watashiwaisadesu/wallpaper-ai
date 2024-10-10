from sqlalchemy.orm import Session
from fastapi import APIRouter, BackgroundTasks, Depends, status, Header

from app.core import get_db
from app.responses import LoginResponse
from app.schemas import LoginRequest, EmailRequest, ResetRequest
from app.auth.services import get_login_token,get_refresh_token,email_forgot_password_link,reset_user_password


guest_router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# Вход пользователя
@guest_router.post("/login", status_code=200, response_model=LoginResponse)
async def user_login(data: LoginRequest, session: Session = Depends(get_db)):
    return await get_login_token(data, session)


# Обновление токена
@guest_router.post("/refresh", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def refresh_token(refresh_token=Header(), session: Session = Depends(get_db)):
    return await get_refresh_token(refresh_token, session)


# Сброс пароля
@guest_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: EmailRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_db)):
    await email_forgot_password_link(data, background_tasks, session)
    return {"message": "A email with password reset link has been sent to you."}


# Обновление пароля
@guest_router.put("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetRequest, session: Session = Depends(get_db)):
    await reset_user_password(data, session)
    return {"message": "Your password has been updated."}
