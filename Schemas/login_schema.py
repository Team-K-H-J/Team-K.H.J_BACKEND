from pydantic import BaseModel, EmailStr, Field

#로그인 스키마
class loginData(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    email: EmailStr


class LoginResponse(BaseModel):
    message: str
    is_admin: bool
