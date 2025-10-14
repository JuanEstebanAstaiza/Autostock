"""
Router de autenticación para Autostock
Maneja login, logout y verificación de tokens
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import get_db
from auth import authenticate_user, create_access_token, get_current_user, get_current_user_from_cookie
from models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login")
async def login_page(request: Request):
    """Mostrar página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Procesar login y redirigir según rol"""
    print(f"Login attempt: username={username}")  # Debug

    user = authenticate_user(db, username, password)
    print(f"Authentication result: {user is not None}")  # Debug

    if not user:
        print("Authentication failed - returning login page with error")  # Debug
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales inválidas"}
        )

    print(f"Authentication successful for user: {user.nombre_usuario} (role: {user.rol})")  # Debug

    # Crear token de acceso
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.nombre_usuario,
            "role": user.rol,
            "negocio_id": user.negocio_id
        },
        expires_delta=access_token_expires
    )

    print(f"Token created successfully")  # Debug

    # Crear respuesta con cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,  # Sin prefijo "Bearer"
        httponly=True,
        max_age=1800,  # 30 minutos
        expires=1800,
        samesite="lax"  # Para compatibilidad con navegadores
    )

    print(f"Redirecting to dashboard")  # Debug
    return response

@router.post("/logout")
async def logout():
    """Cerrar sesión eliminando cookie"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response

@router.get("/dashboard")
async def dashboard(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    """Redirigir al dashboard correspondiente según rol"""
    if current_user.rol == "superadmin":
        return RedirectResponse(url="/superadmin/dashboard", status_code=302)
    elif current_user.rol == "admin":
        return RedirectResponse(url="/negocio/dashboard", status_code=302)
    elif current_user.rol == "vendedor":
        return RedirectResponse(url="/vendedor/dashboard", status_code=302)
    else:
        raise HTTPException(status_code=403, detail="Rol no reconocido")

@router.get("/api/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtener información del usuario actual (para API)"""
    return {
        "id": current_user.id,
        "username": current_user.nombre_usuario,
        "role": current_user.rol,
        "negocio_id": current_user.negocio_id,
        "estado": current_user.estado
    }
