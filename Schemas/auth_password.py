from pydantic import BaseModel

#비밀번호 일치 여부 스키마
class password_schema(BaseModel):
    password: str
    