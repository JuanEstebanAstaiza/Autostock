"""
Módulo de autenticación JWT para Autostock
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import hashlib

from models import get_db
from models.user import User

# Configuración JWT
SECRET_KEY = "autostock_secret_key_2024"  # En producción, usar variable de entorno
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Configuración de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Seguridad HTTP Bearer
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña usando hash SHA256 (por simplicidad)"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """Crear hash de contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Autenticar usuario por nombre de usuario y contraseña"""
    user = db.query(User).filter(User.nombre_usuario == username).first()
    if not user:
        return None
    if not verify_password(password, user.contraseña):
        return None
    if user.estado != "activo":
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token de acceso JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificar token JWT desde header Authorization"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        negocio_id: Optional[int] = payload.get("negocio_id")

        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username, "role": role, "negocio_id": negocio_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token_from_cookie(request: Request):
    """Verificar token JWT desde cookie (para rutas web)"""
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        # El token ya viene limpio sin prefijo "Bearer "

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        negocio_id: Optional[int] = payload.get("negocio_id")

        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        return {"username": username, "role": role, "negocio_id": negocio_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

def get_current_user(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Obtener usuario actual desde token (para API)"""
    user = db.query(User).filter(User.nombre_usuario == token_data["username"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Obtener usuario actual desde cookie (para rutas web)"""
    token_data = verify_token_from_cookie(request)
    user = db.query(User).filter(User.nombre_usuario == token_data["username"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

def require_role(required_role: str):
    """Dependencia para requerir un rol específico (API)"""
    def role_checker(token_data: dict = Depends(verify_token)):
        if token_data["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {required_role}"
            )
        return token_data
    return role_checker

def require_role_from_cookie(required_role: str):
    """Dependencia para requerir un rol específico desde cookie (web)"""
    def role_checker(request: Request, db: Session = Depends(get_db)):
        token_data = verify_token_from_cookie(request)
        if token_data["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {required_role}"
            )
        user = db.query(User).filter(User.nombre_usuario == token_data["username"]).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return user
    return role_checker

# Dependencias específicas por rol (API)
require_superadmin = require_role("superadmin")
require_admin = require_role("admin")
require_vendedor = require_role("vendedor")

# Dependencias específicas por rol desde cookie (web)
require_superadmin_from_cookie = require_role_from_cookie("superadmin")
require_admin_from_cookie = require_role_from_cookie("admin")
require_vendedor_from_cookie = require_role_from_cookie("vendedor")

def require_admin_or_superadmin(token_data: dict = Depends(verify_token)):
    """Permitir acceso a administradores o superadministradores (API)"""
    if token_data["role"] not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de administrador"
        )
    return token_data

def require_admin_or_superadmin_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Permitir acceso a administradores o superadministradores desde cookie (web)"""
    token_data = verify_token_from_cookie(request)
    if token_data["role"] not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de administrador"
        )
    user = db.query(User).filter(User.nombre_usuario == token_data["username"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

def require_same_business(user: User = Depends(get_current_user), token_data: dict = Depends(verify_token)):
    """Verificar que el usuario pertenezca al mismo negocio (para admins) - API"""
    if token_data["role"] == "admin" and user.negocio_id != token_data["negocio_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. No pertenece al negocio correcto"
        )
    return user

def require_same_business_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Verificar que el usuario pertenezca al mismo negocio (para admins) - web"""
    token_data = verify_token_from_cookie(request)
    user = db.query(User).filter(User.nombre_usuario == token_data["username"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if token_data["role"] == "admin" and user.negocio_id != token_data["negocio_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. No pertenece al negocio correcto"
        )
    return user
