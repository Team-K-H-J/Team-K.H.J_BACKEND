from pydantic import BaseModel, model_validator
from Schemas.fields import Password

#비밀번호 일치 여부 스키마
class password_schema(BaseModel):
    password: str


class new_password_schema(BaseModel):
    password: Password
    password_confirm: str | None = None

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password_confirm is not None and self.password != self.password_confirm:
            raise ValueError("비밀번호가 일치하지 않습니다.")
        return self
