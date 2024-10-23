from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException
import logging

from app.core import get_async_db, settings_env
from app.auth.responses import UserResponse
from app.auth.schemas import RegisterUserRequest, VerifyUserRequest
from app.auth.services import create_user_service, activate_user_service, get_current_user, logout_user_service

settings = settings_env
logger = logging.getLogger(__name__)

user_router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@user_router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user_account(
        data: RegisterUserRequest,
        backgroundTasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_db)):
    logger.debug("Attempting to create user account.")
    try:
        user_response = await create_user_service(data, backgroundTasks, session)
        logger.info(f"User account created successfully: {user_response.email}")
        return user_response
    except Exception as e:
        logger.error(f"Error creating user account: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user account: {e}")


@user_router.get("/verify")
async def verify_user_account(
        token: str, email: str,
        backgroundTasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_db)):

    data = VerifyUserRequest(token=token, email=email)
    logger.debug(f"Verifying user account for email: {email}")
    try:
        activation_successful = await activate_user_service(data, backgroundTasks, session)
    except Exception as e:
        logger.error(f"Activation failed for {email}: {e}")
        raise HTTPException(status_code=400, detail="Activation failed.")

    if activation_successful:
        logger.info(f"Activation successful for email: {email}")
        return {"detail": "Activation successful"}
    else:
        logger.warning(f"Activation failed for email: {email}. Token may be invalid or expired.")
        raise HTTPException(status_code=400, detail="Activation failed.")


# Получение текущего пользователя
@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def fetch_user(
        user = Depends(get_current_user)):
    return user

@user_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
        user=Depends(get_current_user),
        session: AsyncSession = Depends(get_async_db)):
    try:
        logger.info(f"User logged out successfully: {user.email}")
        return await logout_user_service(user, session)
    except Exception as e:
        session.rollback()
        logger.error(f"Error during logout for user {user.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Error during logout: {e}")