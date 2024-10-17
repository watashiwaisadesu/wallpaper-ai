from fastapi import APIRouter
from .user.user import user_router
from .user.guest import guest_router
from .user.oauth import oauth_router


auth_router = APIRouter()

auth_router.include_router(user_router)
auth_router.include_router(guest_router)
auth_router.include_router(oauth_router)
