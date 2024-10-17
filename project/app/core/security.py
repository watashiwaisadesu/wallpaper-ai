from passlib.context import CryptContext
from datetime import datetime, timedelta
from password_validator import PasswordValidator
import logging
import jwt
import base64

from app.core import settings_env

logger = logging.getLogger(__name__)
settings = settings_env
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
schema = PasswordValidator()

schema\
    .min(8)\
    .max(100)\
    .has().digits()\
    .has().no().spaces()

def validate(password: str) -> bool:
    is_valid = schema.validate(password)
    logger.debug(f"Password validation result : {is_valid}")
    return is_valid

def hash_password(password):
    logger.debug(f"Hashing password.")
    hashed = pwd_context.hash(password)
    logger.info("Password hashed successfully.")
    return hashed

def verify_password(plain_password, hashed_password):
    logger.debug(f"Verifying password.")
    is_verified = pwd_context.verify(plain_password, hashed_password)
    logger.info(f"Password verification result: {is_verified}")
    return is_verified

def str_encode(string: str) -> str:
    if string is None:
        raise ValueError("Input string cannot be None")
    encoded_string = base64.b85encode(string.encode('ascii')).decode('ascii')
    return encoded_string

def str_decode(string: str) -> str:
    if string is None:
        raise ValueError("Input string cannot be None")
    decoded_string = base64.b85decode(string.encode('ascii')).decode('ascii')
    return decoded_string

def verify_token(user_token, token):
    logger.debug("Verifying token.")
    try:
        result = verify_password(user_token, token)
        logger.info("Token verification successful.")
        return result
    except Exception as e:
        logger.exception("Token verification failed.")
        return False

def generate_token(payload: dict, secret: str, algo: str, expiry: timedelta):
    logger.debug("Generating JWT token.")
    expire = datetime.utcnow() + expiry
    payload.update({"exp": expire})
    token = jwt.encode(payload, secret, algorithm=algo)
    logger.info("JWT token generated successfully.")
    return token

def get_token_payload(token: str, secret: str, algo: str):
    logger.debug("Decoding JWT token payload.")
    try:
        payload = jwt.decode(token, secret, algorithms=[algo])
        logger.info("JWT token payload decoded successfully.")
    except Exception as jwt_exec:
        logger.exception(f"JWT Error: {str(jwt_exec)}")
        payload = None
    return payload
