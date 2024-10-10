from sqlalchemy.orm import Session
from fastapi import APIRouter, BackgroundTasks, Depends, status, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.core import get_db, settings_env
from app.responses import UserResponse
from app.auth.schemas import RegisterUserRequest, VerifyUserRequest
from app.auth.services import create_user_account_service, activate_user_account, get_current_user

settings = settings_env
templates = Jinja2Templates(directory="app/templates")

user_router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# Создание аккаунта пользователя
@user_router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user_account(data: RegisterUserRequest, backgroundTasks: BackgroundTasks, session: Session = Depends(get_db)):
    try:
        return await create_user_account_service(data, backgroundTasks, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user account: {e}")


@user_router.get("/verify")
async def verify_user_account(request: Request, token: str, email: str, backgroundTasks: BackgroundTasks, session: Session = Depends(get_db)):
    data = VerifyUserRequest(token=token, email=email)
    try:
        activation_successful = await activate_user_account(data, backgroundTasks, session)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Activation failed.")
    
    if activation_successful:
        return templates.TemplateResponse("account_activated.html", {"request": request})
    else:
        raise HTTPException(status_code=400, detail="Activation failed.")


# Получение текущего пользователя
@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def fetch_user(user = Depends(get_current_user)):
    return user

