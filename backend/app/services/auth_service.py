from fastapi import HTTPException, status
from app.database import db
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema
from app.utils.validators import validate_email, validate_password_strength, validate_username
from app.services.facial_recognition_service import FacialRecognitionService
from datetime import timedelta, datetime, timezone
import uuid
import base64


class AuthService:
    """
    Servicio de autenticación que maneja toda la lógica de negocio relacionada
    con el registro y login de usuarios
    """
    
    @staticmethod
    async def register_user(user_data: UserRegisterSchema) -> dict:
        """
        Registra un nuevo usuario en la base de datos
        
        Args:
            user_data: Datos del usuario a registrar
            
        Returns:
            Datos del usuario creado
            
        Raises:
            HTTPException: Si el usuario ya existe o los datos no son válidos
        """
        # Validaciones
        if not validate_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email inválido"
            )
        
        if not validate_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nombre de usuario inválido (3-50 caracteres, solo letras, números y guiones bajos)"
            )
        
        is_valid, message = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Verificar si el usuario ya existe
        existing_user = db.collection("users").where("email", "==", user_data.email).stream()
        if list(existing_user):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado"
            )
        
        # ✅ VERIFICACIÓN TEMPRANA: Si se proporciona imagen facial, verificar unicidad ANTES de crear el usuario
        if user_data.facial_image_base64:
            try:
                image_data = base64.b64decode(user_data.facial_image_base64)
                facial_service = FacialRecognitionService()
                
                # Verificar que el rostro sea único
                facial_uniqueness = facial_service.check_facial_uniqueness(image_data)
                
                if not facial_uniqueness["is_unique"]:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"⛔ El rostro ya está registrado en el sistema. No se pueden registrar dos usuarios con el mismo rostro. "
                               f"Usuario coincidente: {facial_uniqueness['matched_user_id']} "
                               f"(Confianza: {facial_uniqueness['confidence']}%). "
                               f"Por favor, intenta con una foto diferente o un usuario diferente."
                    )
            except HTTPException:
                # Re-lanzar HTTPException tal cual
                raise
            except Exception as e:
                print(f"[ERROR] Error verificando facial en registro: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error procesando imagen facial: {str(e)}"
                )
        
        # Crear nuevo usuario
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        user_dict = {
            "user_id": user_id,
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name or "",
            "hashed_password": hash_password(user_data.password),
            "is_active": True,
            "two_factor_enabled": False,
            "facial_recognition_enabled": False,
            "created_at": now,
            "updated_at": now
        }
        
        # Guardar en Firestore
        db.collection("users").document(user_id).set(user_dict)
        
        # Si se proporciona imagen facial, guardarla (ya fue verificada arriba)
        if user_data.facial_image_base64:
            try:
                # Decodificar imagen base64
                image_data = base64.b64decode(user_data.facial_image_base64)
                
                # Guardar imagen usando el servicio de reconocimiento facial
                facial_service = FacialRecognitionService()
                facial_service.save_facial_image(image_data, user_id)
                
                # Marcar que el usuario tiene reconocimiento facial habilitado
                db.collection("users").document(user_id).update({
                    "facial_recognition_enabled": True,
                    "updated_at": datetime.now(timezone.utc)
                })
                
                user_dict["facial_recognition_enabled"] = True
                print(f"[FACIAL] Imagen facial guardada para usuario {user_id}")
            except Exception as e:
                print(f"[ERROR] Error guardando imagen facial después de verificación: {str(e)}")
                # Eliminar el usuario si hay error guardando la imagen
                db.collection("users").document(user_id).delete()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error guardando imagen facial: {str(e)}"
                )
        
        # Retornar sin la contraseña hasheada
        user_dict.pop("hashed_password")
        return user_dict
    
    @staticmethod
    async def login_user(login_data: UserLoginSchema) -> dict:
        """
        Autentica un usuario y genera un token JWT
        
        Args:
            login_data: Credenciales del usuario
            
        Returns:
            Token de acceso y datos del usuario
            
        Raises:
            HTTPException: Si las credenciales son inválidas
        """
        # Buscar usuario por email
        user_query = db.collection("users").where("email", "==", login_data.email).stream()
        user_docs = list(user_query)
        
        if not user_docs:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        user_data = user_docs[0].to_dict()
        
        # Verificar contraseña
        if not verify_password(login_data.password, user_data.get("hashed_password", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Verificar si el usuario está activo
        if not user_data.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        # Crear token JWT
        access_token = create_access_token(
            data={"sub": user_data["user_id"], "email": user_data["email"]}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": {
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "full_name": user_data.get("full_name", ""),
                "two_factor_enabled": user_data.get("two_factor_enabled", False),
                "facial_recognition_enabled": user_data.get("facial_recognition_enabled", False)
            }
        }
