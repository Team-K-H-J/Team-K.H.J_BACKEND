from pydantic import BaseModel
from Schemas.fields import DeviceID

#알림 설정시 스키마
class user_want_device(BaseModel):
    device_id: DeviceID
