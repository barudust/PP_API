# dependencies.py
"""
Capa de seguridad / control de acceso (RBAC).

Provee las dependencias de FastAPI para:
  - Autenticar al usuario a partir del token JWT (`get_current_user`).
  - Restringir endpoints por rol (`require_roles`).

Roles canónicos (en minúsculas): 'vendedor', 'gerente', 'superadmin'.
`superadmin` SIEMPRE pasa cualquier verificación de rol.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.database import database
from app.models import usuario

# --- Roles canónicos ---
ROL_VENDEDOR = "vendedor"
ROL_GERENTE = "gerente"
ROL_SUPERADMIN = "superadmin"

ROLES_VALIDOS = {ROL_VENDEDOR, ROL_GERENTE, ROL_SUPERADMIN}

# tokenUrl solo se usa para la documentación interactiva (/docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

_CRED_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decodifica el JWT, valida y devuelve el registro del usuario desde la BD."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("id")
        if user_id is None:
            raise _CRED_EXC
    except JWTError:
        raise _CRED_EXC

    user = await database.fetch_one(select(usuario).where(usuario.c.id == user_id))
    if user is None:
        raise _CRED_EXC
    return user


def require_roles(*roles: str):
    """
    Fábrica de dependencias: exige que el usuario tenga uno de los roles dados.
    `superadmin` se agrega implícitamente (siempre autorizado).

    Uso:
        @router.post("/", dependencies=[Depends(require_roles(ROL_GERENTE))])
        # o para leer al usuario:
        async def endpoint(actual = Depends(require_roles(ROL_GERENTE))): ...
    """
    permitidos = {r.lower() for r in roles} | {ROL_SUPERADMIN}

    async def _checker(actual=Depends(get_current_user)):
        rol = (actual["rol"] or "").lower()
        if rol not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )
        return actual

    return _checker


def require_perm(*codigos: str):
    """
    Fábrica de dependencias por PERMISO (no por rol hardcodeado).
    Autoriza si el rol del usuario tiene al menos uno de los permisos dados.
    `superadmin` siempre pasa.

    Uso:
        @router.post("/", dependencies=[Depends(require_perm("pos.vender"))])
    """
    requeridos = set(codigos)

    async def _checker(actual=Depends(get_current_user)):
        # Import local para evitar ciclo de importación en el arranque.
        from app.services.permisos_service import permisos_de_rol

        rol = (actual["rol"] or "").lower()
        if rol == ROL_SUPERADMIN:
            return actual
        permisos = set(await permisos_de_rol(rol))
        if requeridos & permisos:
            return actual
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requiere permiso: {' o '.join(sorted(requeridos))}",
        )

    return _checker
