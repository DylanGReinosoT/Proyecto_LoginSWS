from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user_schema import UserResponseSchema, UserUpdateSchema
from app.services.user_service import UserService
from app.core.security import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserResponseSchema)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Obtiene el perfil del usuario autenticado
    """
    user = await UserService.get_user_by_id(current_user["user_id"])
    return user


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Obtiene la información de un usuario específico (requiere autenticación)
    """
    user = await UserService.get_user_by_id(user_id)
    return user


@router.put("/me", response_model=UserResponseSchema)
async def update_user_profile(
    update_data: UserUpdateSchema,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza el perfil del usuario autenticado
    """
    update_dict = update_data.dict(exclude_unset=True)
    user = await UserService.update_user(current_user["user_id"], update_dict)
    return user


@router.post("/facial-recognition/enable")
async def enable_facial_recognition(current_user: dict = Depends(get_current_user)):
    """
    Habilita autenticación con reconocimiento facial para el usuario
    """
    user = await UserService.enable_facial_recognition(current_user["user_id"])
    return {
        "message": "Reconocimiento facial habilitado",
        "user": user
    }


@router.post("/facial-recognition/disable")
async def disable_facial_recognition(current_user: dict = Depends(get_current_user)):
    """
    Desactiva autenticación con reconocimiento facial para el usuario
    """
    user = await UserService.disable_facial_recognition(current_user["user_id"])
    return {
        "message": "Reconocimiento facial deshabilitado",
        "user": user
    }


@router.get("/health")
async def health_check():
    """
    Verifica que el servicio de usuarios esté funcionando
    """
    return {"status": "healthy", "service": "users"}
