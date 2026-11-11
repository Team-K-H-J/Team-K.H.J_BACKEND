from fastapi import APIRouter, Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from database.connection import Create_db
from Schemas.senser_schema import Device_State, TelemetryData
from services.devices import apply_telemetry, require_device_key

router_dev = APIRouter()
device_key = APIKeyHeader(name="X-Device-Key", scheme_name="DeviceKey", auto_error=False)


def state_response(device_id, data):
    return {"success": True, "message": "Success data", "data": {
        "deviceID": device_id, "state": data.state, "Vibration": data.Vibration,
        "V_Data_before": data.V_data_before, "V_Data_After": data.V_data_after,
        "Current": data.Current, "C_Data": data.C_data}}


@router_dev.patch("/api/v1/state/{device_id}")
def update_state(device_id: str, state_data: Device_State, db: Session = Depends(Create_db),
                 x_device_key: str | None = Security(device_key)):
    require_device_key(db, device_id, x_device_key)
    apply_telemetry(db, device_id, state_data)
    return state_response(device_id, state_data)


@router_dev.post("/api/v1/devices/{device_id}/events")
def device_event(device_id: str, data: TelemetryData, db: Session = Depends(Create_db),
                 x_device_key: str | None = Security(device_key)):
    require_device_key(db, device_id, x_device_key)
    applied = apply_telemetry(db, device_id, data)
    response = state_response(device_id, data)
    if data.vibration_hz is not None:
        response["data"]["vibration_hz"] = data.vibration_hz
    return {**response, "applied": applied}
