# security.py
from datetime import datetime, timedelta, timezone
from typing import Union
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuración (En producción esto va en variables de entorno)
SECRET_KEY = "tu_secreto_super_seguro_cambialo_por_algo_largo"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 día

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
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt