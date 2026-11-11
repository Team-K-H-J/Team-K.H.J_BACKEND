from typing import Annotated
from pydantic import AfterValidator, Field


def nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("빈 문자열은 사용할 수 없습니다.")
    return value


Name = Annotated[str, Field(min_length=1, max_length=24), AfterValidator(nonblank)]
StudentNumber = Annotated[str, Field(pattern=r"^[0-9]{4}$")]
Password = Annotated[str, Field(min_length=8, max_length=128)]
DeviceID = Annotated[str, Field(min_length=1, max_length=24), AfterValidator(nonblank)]
