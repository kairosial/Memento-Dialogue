from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    gender: Optional[Gender] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    gender: Optional[Gender] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None


class UserOnboarding(BaseModel):
    privacy_consent: bool
    terms_accepted: bool
    notification_enabled: bool = True


class UserResponse(UserBase):
    id: str
    onboarding_completed: bool
    privacy_consent: bool
    terms_accepted: bool
    notification_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    email: Optional[str] = None