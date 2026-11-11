from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from Schemas.fields import DeviceID, Name, StudentNumber, nonblank
from typing import Annotated
from pydantic import AfterValidator

Title = Annotated[str, Field(min_length=1, max_length=200), AfterValidator(nonblank)]
Content = Annotated[str, Field(min_length=1, max_length=10000), AfterValidator(nonblank)]


class ProfilePatch(BaseModel):
    name: Name | None = None
    number: StudentNumber | None = None
    image_url: HttpUrl | None = None


class SettingsPatch(BaseModel):
    notifications_enabled: bool | None = None
    vibration_enabled: bool | None = None
    theme: Literal["system", "light", "dark"] | None = None
    completed: bool | None = None
    paused: bool | None = None
    stopped: bool | None = None


class NoticeCreate(BaseModel):
    title: Title
    content: Content
    pinned: bool = False


class NoticePatch(BaseModel):
    title: Title | None = None
    content: Content | None = None
    pinned: bool | None = None


class InquiryCreate(BaseModel):
    device_id: DeviceID | None = None
    error_type: Annotated[str, Field(min_length=1, max_length=64), AfterValidator(nonblank)]
    title: Title | None = None
    content: Content


class InquiryStatus(BaseModel):
    status: Literal["unread", "reviewing", "resolved"]


class AvailabilityPatch(BaseModel):
    unavailable: bool
    reason: str | None = Field(default=None, max_length=255)


class PushTokenData(BaseModel):
    token: str = Field(min_length=1, max_length=512)

