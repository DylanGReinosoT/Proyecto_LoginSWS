from fastapi import HTTPException, status
from app.database import db
from app.core.security import hash_password


class UserService:
    """
    Servicio de usuarios que maneja toda la lógica de negocio relacionada
    con la gestión de usuarios
    """
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> dict:
        """
        Obtiene un usuario por su ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Datos del usuario
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        user_doc = db.collection("users").document(user_id).get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        user_data = user_doc.to_dict()
        user_data.pop("hashed_password", None)  # No devolver la contraseña
        return user_data
    
    @staticmethod
    async def update_user(user_id: str, update_data: dict) -> dict:
        """
        Actualiza los datos de un usuario
        
        Args:
            user_id: ID del usuario
            update_data: Datos a actualizar
            
        Returns:
            Usuario actualizado
        """
        from datetime import datetime, timezone
        
        user_ref = db.collection("users").document(user_id)
        
        if not user_ref.get().exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Si se proporciona una contraseña, hashearla
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = hash_password(update_data["password"])
            del update_data["password"]
        
        # Actualizar timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        user_ref.update(update_data)
        
        updated_user = user_ref.get().to_dict()
        updated_user.pop("hashed_password", None)
        return updated_user
    
    @staticmethod
    async def enable_two_factor(user_id: str) -> dict:
        """
        Habilita autenticación de dos factores para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario actualizado
        """
        return await UserService.update_user(
            user_id,
            {"two_factor_enabled": True}
        )
    
    @staticmethod
    async def enable_facial_recognition(user_id: str) -> dict:
        """
        Habilita reconocimiento facial para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario actualizado
        """
        return await UserService.update_user(
            user_id,
            {"facial_recognition_enabled": True}
        )
    
    @staticmethod
    async def disable_facial_recognition(user_id: str) -> dict:
        """
        Desactiva reconocimiento facial para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario actualizado
        """
        return await UserService.update_user(
            user_id,
            {"facial_recognition_enabled": False}
        )
