# security.py
from datetime import datetime, timedelta, timezone
from typing import Union
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verificar_password(plain_password, hashed_password):
    """Revisa si la contraseña escrita coincide con la encriptada."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Encripta una contraseña."""
    return pwd_context.hash(password)


def crear_token_acceso(data: dict, expires_delta: Union[timedelta, None] = None):
    """Genera el Token JWT que el frontend guardará."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
