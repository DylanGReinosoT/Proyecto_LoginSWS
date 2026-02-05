from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.schemas.facial_schema import (
    FacialCaptureSchema,
    FacialVerificationSchema,
    FacialDetectionResponseSchema,
    FacialVerificationResponseSchema
)
from app.services.facial_recognition_service import FacialRecognitionService
from app.core.security import get_current_user
import base64

router = APIRouter(prefix="/api/facial", tags=["Facial Recognition"])

# Instanciar servicio
facial_service = FacialRecognitionService()


@router.post("/capture", response_model=dict)
async def capture_facial_image(
    facial_data: FacialCaptureSchema,
    current_user: dict = Depends(get_current_user)
):
    """
    Captura y guarda una imagen facial para el usuario autenticado
    
    Requiere:
    - **image_base64**: Imagen en formato base64
    - **description**: Descripción opcional de la captura
    
    Respuesta:
    - **success**: Indicador de éxito
    - **message**: Mensaje de respuesta
    - **filepath**: Ruta del archivo guardado
    """
    try:
        # Decodificar imagen base64
        image_bytes = base64.b64decode(facial_data.image_base64)
        
        # Guardar imagen
        filepath = facial_service.save_facial_image(
            image_bytes,
            current_user["user_id"]
        )
        
        return {
            "success": True,
            "message": "Imagen facial capturada correctamente",
            "filepath": filepath
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/capture-registration", response_model=dict)
async def capture_facial_registration(
    facial_data: FacialCaptureSchema,
    user_id: str = Query(..., description="ID del usuario recién registrado"),
):
    """
    Captura y guarda una imagen facial durante el registro (sin autenticación)
    
    Parámetros query:
    - **user_id**: ID del usuario recién registrado
    
    Body:
    - **image_base64**: Imagen en formato base64
    - **description**: Descripción opcional de la captura
    
    Respuesta:
    - **success**: Indicador de éxito
    - **message**: Mensaje de respuesta
    - **filepath**: Ruta del archivo guardado
    """
    try:
        # Decodificar imagen base64
        image_bytes = base64.b64decode(facial_data.image_base64)
        
        # ✅ NUEVA VERIFICACIÓN: Comprobar que el rostro sea único en el sistema
        facial_uniqueness = facial_service.check_facial_uniqueness(image_bytes, exclude_user_id=user_id)
        
        if not facial_uniqueness["is_unique"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"⛔ El rostro ya está registrado en el sistema. No se pueden registrar dos usuarios con el mismo rostro. "
                       f"Usuario coincidente: {facial_uniqueness['matched_user_id']} "
                       f"(Confianza: {facial_uniqueness['confidence']}%)"
            )
        
        # Guardar imagen
        filepath = facial_service.save_facial_image(
            image_bytes,
            user_id
        )
        
        return {
            "success": True,
            "message": "Imagen facial capturada correctamente",
            "filepath": filepath
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/detect", response_model=FacialDetectionResponseSchema)
async def detect_face(facial_data: FacialCaptureSchema):
    """
    Detecta si hay un rostro en la imagen proporcionada
    
    Requiere:
    - **image_base64**: Imagen en formato base64
    
    Respuesta:
    - **face_detected**: Si se detectó un rostro
    - **message**: Mensaje de respuesta
    - **bbox**: Caja delimitadora del rostro (si se detectó)
    - **confidence**: Confianza de la detección
    """
    try:
        # Decodificar imagen base64
        image_bytes = base64.b64decode(facial_data.image_base64)
        
        # Detectar rostro
        result = facial_service.detect_face_in_image(image_bytes)
        
        return {
            "face_detected": result["face_detected"],
            "message": result["message"],
            "bbox": result.get("bbox"),
            "confidence": result.get("bbox", {}).get("confidence")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify", response_model=FacialVerificationResponseSchema)
async def verify_face(
    facial_data: FacialVerificationSchema,
    current_user: dict = Depends(get_current_user)
):
    """
    Verifica si el rostro coincide con el registrado para el usuario
    
    Requiere autenticación JWT
    
    Requiere:
    - **image_base64**: Imagen en formato base64
    
    Respuesta:
    - **verified**: Si la verificación fue exitosa
    - **message**: Mensaje de respuesta
    - **confidence**: Nivel de confianza de la verificación
    """
    try:
        # Decodificar imagen base64
        image_bytes = base64.b64decode(facial_data.image_base64)
        
        # Verificar rostro
        result = facial_service.verify_face(
            image_bytes,
            current_user["user_id"]
        )
        
        return {
            "verified": result["verified"],
            "message": result["message"],
            "confidence": result.get("confidence", 0.9)
        }
    except HTTPException as he:
        # Re-lanzar excepciones HTTP con código apropiado
        print(f"[FACIAL_VERIFY] HTTPException: {he.detail} (Status: {he.status_code})")
        raise he
    except Exception as e:
        print(f"[ERROR] verify_face: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la verificación facial: {str(e)}"
        )

@router.post("/check-uniqueness")
async def check_facial_uniqueness(facial_data: FacialCaptureSchema):
    """
    Verifica si un rostro es único en el sistema (no pertenece a otro usuario)
    
    Se usa durante el registro para validar que el rostro no esté duplicado
    
    Requiere:
    - **image_base64**: Imagen en formato base64
    
    Respuesta:
    - **is_unique**: Si el rostro es único
    - **message**: Mensaje descriptivo
    - **matched_user_id**: ID del usuario si ya existe ese rostro
    - **confidence**: Confianza de la coincidencia si existe
    """
    try:
        # Decodificar imagen base64
        image_bytes = base64.b64decode(facial_data.image_base64)
        
        # Verificar unicidad del rostro
        result = facial_service.check_facial_uniqueness(image_bytes)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-images")
async def get_my_facial_images(current_user: dict = Depends(get_current_user)):
    """
    Obtiene todas las imágenes faciales guardadas del usuario autenticado
    
    Requiere autenticación JWT
    
    Respuesta:
    - **images**: Lista de rutas de imágenes
    - **count**: Número de imágenes
    """
    images = facial_service.get_user_facial_images(current_user["user_id"])
    
    return {
        "images": images,
        "count": len(images)
    }


@router.get("/health")
async def health_check():
    """
    Verifica que el servicio de reconocimiento facial esté funcionando
    """
    return {
        "status": "healthy",
        "service": "facial_recognition"
    }
