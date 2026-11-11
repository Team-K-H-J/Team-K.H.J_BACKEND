import math
from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    AliasChoices,
    BaseModel,
    Field,
    FiniteFloat,
    field_validator,
    model_validator,
)

from Schemas.fields import DeviceID
from services.common import utc

SensorState = Literal["used", "not_used", "paused", "error"]


def valid_measured_at(value: datetime) -> datetime:
    try:
        year = utc(value).year
    except OverflowError:
        year = 0
    if year < 1000:
        raise ValueError("측정 시각은 MySQL DATETIME 범위 안의 UTC 시각이어야 합니다.")
    return value


MeasuredAt = Annotated[datetime, AfterValidator(valid_measured_at)]


class Device_State(BaseModel):
    state: SensorState
    Vibration: bool
    V_data_before: list[FiniteFloat] = Field(min_length=3, max_length=3, validation_alias=AliasChoices("V_Data_before", "V_data_before"))
    V_data_after: list[FiniteFloat] = Field(min_length=3, max_length=3, validation_alias=AliasChoices("V_Data_After", "V_data_after"))
    Current: bool
    C_data: str = Field(max_length=64, validation_alias=AliasChoices("C_Data", "C_data"))
    device_id: DeviceID | None = None
    event_id: str | None = Field(default=None, min_length=1, max_length=64)
    measured_at: MeasuredAt | None = None
    sensor_error: str | None = Field(default=None, max_length=255)

    @field_validator("C_data")
    @classmethod
    def valid_current(cls, value):
        if value is None:
            return value
        try:
            current = float(value)
        except ValueError:
            raise ValueError("전류값은 숫자 문자열이어야 합니다.") from None
        if not math.isfinite(current) or current < 0:
            raise ValueError("전류값은 유한한 0 이상의 값이어야 합니다.")
        return value

    @model_validator(mode="after")
    def consistent_detection(self):
        if self.state is None:
            if self.sensor_error:
                self.state = "error"
            else:
                self.state = "used" if self.Current and self.Vibration else "not_used"
        if self.state == "used" and not (self.Current and self.Vibration):
            raise ValueError("사용 중 상태는 전류와 진동이 동시에 감지되어야 합니다.")
        if self.state == "not_used" and self.Current and self.Vibration:
            raise ValueError("전류와 진동이 모두 감지된 상태는 사용 종료로 처리할 수 없습니다.")
        return self


class TelemetryData(Device_State):
    event_id: str = Field(min_length=1, max_length=64)
    measured_at: MeasuredAt
    state: SensorState | None = None
    Vibration: bool | None = None
    V_data_before: list[FiniteFloat] | None = Field(
        default=None, min_length=3, max_length=3, validation_alias=AliasChoices("V_Data_before", "V_data_before"))
    V_data_after: list[FiniteFloat] | None = Field(
        default=None, min_length=3, max_length=3, validation_alias=AliasChoices("V_Data_After", "V_data_after"))
    Current: bool | None = None
    C_data: str | None = Field(default=None, max_length=64,
                               validation_alias=AliasChoices("C_Data", "C_data"))
    vibration_hz: FiniteFloat | None = Field(default=None, ge=0)

    @field_validator("C_data", mode="before", json_schema_input_type=str | float | None)
    @classmethod
    def current_as_text(cls, value):
        if type(value) in (int, float):
            return str(value)
        return value

    @model_validator(mode="after")
    def complete_measurement(self):
        if (self.V_data_before is None) != (self.V_data_after is None):
            raise ValueError("측정 전후 가속도 배열을 함께 전송해 주세요.")
        if self.state != "error":
            if self.Current is None or self.Vibration is None or self.C_data is None:
                raise ValueError("전류·진동 감지 여부와 전류 측정값이 필요합니다.")
            if self.V_data_before is None and self.vibration_hz is None:
                raise ValueError("측정 전후 가속도 배열 또는 진동수가 필요합니다.")
        return self
