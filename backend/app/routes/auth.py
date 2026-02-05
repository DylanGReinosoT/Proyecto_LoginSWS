from fastapi import APIRouter, HTTPException, status, Query
from app.schemas.user_schema import UserRegisterSchema, UserLoginSchema, UserResponseSchema, RegistrationFlowResponseSchema, LoginFlowResponseSchema
from app.schemas.token_schema import TokenResponseSchema
from app.schemas.facial_schema import FacialCaptureSchema
from app.services.auth_service import AuthService
from app.services.facial_recognition_service import FacialRecognitionService
import base64

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Instanciar servicios
facial_service = FacialRecognitionService()


@router.post("/register", response_model=RegistrationFlowResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegisterSchema):
    """
    Registra un nuevo usuario en el sistema
    
    - **email**: Email del usuario (debe ser único)
    - **username**: Nombre de usuario (3-50 caracteres)
    - **password**: Contraseña (mín. 8 caracteres)
    - **full_name**: Nombre completo (opcional)
    
    Respuesta incluye indicación para capturar facial en el siguiente paso
    """
    user = await AuthService.register_user(user_data)
    return {
        **user,
        "message": "Usuario registrado correctamente. Por favor, capture una foto facial para completar el proceso.",
        "next_step": "facial_capture"
    }


@router.post("/login", response_model=LoginFlowResponseSchema)
async def login(login_data: UserLoginSchema):
    """
    Autentica un usuario y devuelve un token JWT
    
    - **email**: Email del usuario
    - **password**: Contraseña
    
    Respuesta incluye:
    - **access_token**: Token JWT para autenticación
    - **token_type**: Tipo de token (bearer)
    - **expires_in**: Tiempo de expiración en segundos
    - **next_step**: facial_verification (indica que debe verificar rostro)
    """
    result = await AuthService.login_user(login_data)
    user_data = result.get("user_data", {})
    
    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"],
        "expires_in": 1800,  # 30 minutos
        "user_id": user_data.get("user_id", ""),
        "message": "Credenciales válidas. Por favor, verifique su identidad facial.",
        "next_step": "facial_verification",
        "facial_recognition_enabled": user_data.get("facial_recognition_enabled", False)
    }


@router.post("/verify-facial-for-login")
async def verify_facial_for_login(
    facial_data: FacialCaptureSchema,
    user_id: str = Query(..., description="ID del usuario que intenta hacer login")
):
    """
    ✅ VERIFICACIÓN CRÍTICA: Verifica que el rostro pertenezca al usuario durante el login
    
    Esta es una ruta de seguridad adicional que garantiza que:
    - El rostro capturado pertenece al usuario especificado
    - No se puede usar un rostro de otro usuario para hacerse pasar por alguien más
    
    Parámetros query:
    - **user_id**: ID del usuario que intenta hacer login
    
    Body:
    - **image_base64**: Imagen facial en formato base64
    
    Respuesta:
    - **verified**: True si el rostro coincide con el usuario
    - **message**: Mensaje de resultado
    - **confidence**: Nivel de confianza de la verificación
    """
    try:
        # Decodificar imagen base64
        image_bytes = base64.b64decode(facial_data.image_base64)
        
        # ✅ VERIFICACIÓN ESTRICTA: El rostro debe pertenecer al usuario específico
        result = facial_service.verify_face_for_login(image_bytes, user_id)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en verificación facial: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Verifica que el servicio de autenticación esté funcionando
    """
    return {"status": "healthy", "service": "authentication"}
