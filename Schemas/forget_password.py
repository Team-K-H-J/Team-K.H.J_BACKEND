from pydantic import BaseModel, EmailStr
from Schemas.fields import Name, StudentNumber

#비밀번호 잋음
class password_forget(BaseModel):
    email: EmailStr
    name: Name
    number: StudentNumber
