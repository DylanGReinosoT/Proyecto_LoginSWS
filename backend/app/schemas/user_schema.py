from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    facial_image_base64: Optional[str] = None  # Imagen facial en base64 (capturada antes)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponseSchema(BaseModel):
    user_id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    two_factor_enabled: bool
    facial_recognition_enabled: bool

    class Config:
        from_attributes = True


class RegistrationFlowResponseSchema(BaseModel):
    """Respuesta después del registro inicial con instrucciones para captura facial"""
    user_id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    message: str
    next_step: str = "facial_capture"  # Indica que el siguiente paso es capturar facial
    
    class Config:
        from_attributes = True


class LoginFlowResponseSchema(BaseModel):
    """Respuesta después del login para captura facial"""
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    message: str
    next_step: str = "facial_verification"  # Indica que el siguiente paso es verificar facial
    facial_recognition_enabled: bool  # Si ya tiene facial registrado
