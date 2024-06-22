from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from src.database.models import Role
from typing import Optional

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: datetime
    extra_data: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    pass

class Contact(ContactBase):
    id: int

    class Config:
        orm_mode = True


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    id: int = 1
    username: str
    email: EmailStr
    avatar: str
    role: Role

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    
class RequestEmail(BaseModel):
    email: EmailStr
