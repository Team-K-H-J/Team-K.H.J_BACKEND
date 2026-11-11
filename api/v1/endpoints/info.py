import os
from fastapi import APIRouter

router_info = APIRouter()


@router_info.get("/api/v1/info")
def app_info():
    return {"app_version": os.getenv("APP_VERSION", "0.1.0"),
            "terms_url": os.getenv("TERMS_URL"), "privacy_url": os.getenv("PRIVACY_URL"),
            "push_configured": bool(os.getenv("FCM_PROJECT_ID")),
            "poll_interval_seconds": 5}
