from pydantic import BaseModel, EmailStr, model_validator
from Schemas.fields import Name, Password, StudentNumber

#회원가입 스키마
class SignupData(BaseModel):
    password: Password
    name: Name
    number: StudentNumber
    email: EmailStr
    password_confirm: str | None = None

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password_confirm is not None and self.password != self.password_confirm:
            raise ValueError("비밀번호가 일치하지 않습니다.")
        return self
