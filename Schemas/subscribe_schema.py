from pydantic import BaseModel

#알림 설정시 스키마
class user_want_device(BaseModel):
    device_id: str