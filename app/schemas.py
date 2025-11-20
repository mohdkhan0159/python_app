from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class CourseBase(BaseModel):
    title: str
    description: Optional[str]
    price_cents: int

class CourseOut(CourseBase):
    id: int
    thumbnail_path: Optional[str]
    class Config:
        from_attributes = True
