import logging
from sqlalchemy.orm import Session
from fastapi import APIRouter, BackgroundTasks, Depends, status, Header, HTTPException, Request, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.database import get_db
from app.responses.user import UserResponse, LoginResponse
from app.auth.schemas.user import RegisterUserRequest, VerifyUserRequest, LoginRequest, EmailRequest, ResetRequest
from app.auth.services import user
from app.core.config import settings_env
from app.core import security

settings = settings_env
templates = Jinja2Templates(directory="app/templates")

# Инициализация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth2 схемы
google_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token"
)

github_oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://github.com/login/oauth/authorize",
    tokenUrl="https://github.com/login/oauth/access_token"
)

# Роутеры
user_router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

guest_router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

oauth_router = APIRouter(
    prefix="/oauth",
    tags=["OAuth"]
)

# Google Login
@oauth_router.get('/google-login')
async def login(request: Request):
    logger.info("Starting Google login process")
    logger.debug(f"GOOGLE_CLIENT_ID: {settings.GOOGLE_CLIENT_ID}")
    logger.debug(f"GOOGLE_REDIRECT_URI: {settings.GOOGLE_REDIRECT_URI}")
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline")


# Google auth callback
@oauth_router.get('/auth/google')
async def auth_google(code: str, session: Session = Depends(get_db)):
    logger.info("Received Google auth callback")
    provider = "google"
    return await user.get_auth_callback(code, provider, session)


# Создание аккаунта пользователя
@user_router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user_account(data: RegisterUserRequest, backgroundTasks: BackgroundTasks, session: Session = Depends(get_db)):
    logger.info(f"Creating user account for email: {data.email}")
    try:
        return await user.create_user_account(data, backgroundTasks, session)
    except Exception as e:
        logger.error(f"Error creating user account: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


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
    return await user.activate_user_account(data, backgroundTasks, session)


# Получение текущего пользователя
@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def fetch_user(user = Depends(security.get_current_user)):
    logger.info(f"Fetching current user: {user.email}")
    return user


# Вход пользователя
@guest_router.post("/login", status_code=200, response_model=LoginResponse)
async def user_login(data: LoginRequest, session: Session = Depends(get_db)):
    logger.info(f"User login attempt: {data.email}")
    return await user.get_login_token(data, session)


# Обновление токена
@guest_router.post("/refresh", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def refresh_token(refresh_token=Header(), session: Session = Depends(get_db)):
    logger.info("Refreshing token")
    return await user.get_refresh_token(refresh_token, session)


# Сброс пароля
@guest_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: EmailRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_db)):
    logger.info(f"Forgot password request for email: {data.email}")
    await user.email_forgot_password_link(data, background_tasks, session)
    return {"message": "A email with password reset link has been sent to you."}


# Обновление пароля
@guest_router.put("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetRequest, session: Session = Depends(get_db)):
    logger.info(f"Resetting password for email: {data.email}")
    await user.reset_user_password(data, session)
    return {"message": "Your password has been updated."}
