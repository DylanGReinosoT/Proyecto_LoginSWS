from pydantic import BaseModel
from typing import Optional


class FacialCaptureSchema(BaseModel):
    """Esquema para captura de imagen facial en base64"""
    image_base64: str
    description: Optional[str] = None


class FacialVerificationSchema(BaseModel):
    """Esquema para verificación de imagen facial"""
    image_base64: str


class FacialDetectionResponseSchema(BaseModel):
    """Respuesta de detección facial"""
    face_detected: bool
    message: str
    bbox: Optional[dict] = None
    confidence: Optional[float] = None


class FacialVerificationResponseSchema(BaseModel):
    """Respuesta de verificación facial"""
    verified: bool
    message: str
    confidence: float


class FacialUniquenessResponseSchema(BaseModel):
    """Respuesta de verificación de unicidad facial"""
    is_unique: bool
    message: str
    matched_user_id: Optional[str] = None
    confidence: float

