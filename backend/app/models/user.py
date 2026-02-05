from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(UserBase):
    user_id: str
    hashed_password: str
    is_active: bool = True
    two_factor_enabled: bool = False
    facial_recognition_enabled: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserResponse(UserBase):
    user_id: str
    is_active: bool
    two_factor_enabled: bool
    facial_recognition_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True
