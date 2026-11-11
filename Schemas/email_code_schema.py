from pydantic import BaseModel, EmailStr, Field

#이메일 인증 번호 스키마
class email_code_schema(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^[0-9]{6}$")
