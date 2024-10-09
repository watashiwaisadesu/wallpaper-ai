import logging
from sqlalchemy.orm import Session
from fastapi import APIRouter, BackgroundTasks, Depends, status, Header, HTTPException, Request, Security
from fastapi.templating import Jinja2Templates

from app.core import get_db, settings_env
from app.responses import UserResponse
from app.auth.schemas import RegisterUserRequest, VerifyUserRequest, LoginRequest, EmailRequest, ResetRequest
from app.auth.services import create_user_account_service, activate_user_account, get_current_user


settings = settings_env
templates = Jinja2Templates(directory="app/templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


user_router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# Создание аккаунта пользователя
@user_router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user_account(data: RegisterUserRequest, backgroundTasks: BackgroundTasks, session: Session = Depends(get_db)):
    logger.info(f"Creating user account for email: {data.email}")
    try:
        return await create_user_account_service(data, backgroundTasks, session)
    except Exception as e:
        logger.error(f"Error creating user account: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user account: {e}")


# Проверка пользователя (GET)
@user_router.get('/verify')
async def verify_user_account_get(request: Request, token: str, email: str, backgroundTasks: BackgroundTasks, session: Session = Depends(get_db)):
    logger.info(f"Verifying user account for email: {email}")
    data = VerifyUserRequest(token=token, email=email)

    try:
        activation_successful = await verify_user_account(data, backgroundTasks, session)
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        raise HTTPException(status_code=400, detail="Activation failed.")
    
    if activation_successful:
        logger.info(f"Account activated successfully for email: {email}")
        return templates.TemplateResponse("account_activated.html", {"request": request})
    else:
        logger.warning(f"Activation failed for email: {email}")
        raise HTTPException(status_code=400, detail="Activation failed.")


# Проверка пользователя (POST)
@user_router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_user_account(data: VerifyUserRequest, backgroundTasks: BackgroundTasks, session: Session = Depends(get_db)):
    logger.info(f"Verifying user account with token: {data.token}")
    return await activate_user_account(data, backgroundTasks, session)


# Получение текущего пользователя
@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def fetch_user(user = Depends(get_current_user)):
    logger.info(f"Fetching current user: {user.email}")
    return user

