from passlib.context import CryptContext
from datetime import datetime, timedelta
from password_validator import PasswordValidator

import logging
import jwt
import base64

from app.core import settings_env

# Initialize logger
logger = logging.getLogger(__name__)


settings = settings_env
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

schema = PasswordValidator()

schema\
.min(8)\
.max(100)\
.has().digits()\
.has().no().spaces()\
    
    
def validate(password: str) -> bool:
    return schema.validate(password)

    
def hash_password(password):
    logger.debug(f"Hashing password.")
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    logger.debug(f"Verifying password.")
    return pwd_context.verify(plain_password, hashed_password)


def str_encode(string: str) -> str:
    if string is None:
        raise ValueError("Input string cannot be None")
    logger.debug(f"Encoding string: {string}")
    return base64.b85encode(string.encode('ascii')).decode('ascii')


def str_decode(string: str) -> str:
    if string is None:
        raise ValueError("Input string cannot be None")
    logger.debug(f"Decoding string: {string}")
    return base64.b85decode(string.encode('ascii')).decode('ascii')


def verify_token(user_token, token):
    logger.debug("Verifying token.")
    try:
        return verify_password(user_token, token)
    except Exception as e:
        logger.exception("Token verification failed.")
        return False


def generate_token(payload: dict, secret: str, algo: str, expiry: timedelta):
    logger.debug("Generating JWT token.")
    expire = datetime.utcnow() + expiry
    payload.update({"exp": expire})
    return jwt.encode(payload, secret, algorithm=algo)


def get_token_payload(token: str, secret: str, algo: str):
    logger.debug("Decoding JWT token payload.")
    try:
        payload = jwt.decode(token, secret, algorithms=algo)
    except Exception as jwt_exec:
        logger.debug(f"JWT Error: {str(jwt_exec)}")
        payload = None
    return payload


