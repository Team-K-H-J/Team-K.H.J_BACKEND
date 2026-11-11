from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import asyncio
from config import flag
from services.notifications import worker

from api.v1.endpoints.update_state import router_dev
from api.v1.endpoints.login import router_login
from api.v1.endpoints.signup import router_signup
from api.v1.endpoints.load_state import router_load_state
from api.v1.endpoints.logout import router_logout
from api.v1.endpoints.email_contify import router_email
from api.v1.endpoints.password import router_password
from api.v1.endpoints.subscribe import router_subscribe
from api.v1.endpoints.account import router_account
from api.v1.endpoints.devices import router_devices
from api.v1.endpoints.notices import router_notices
from api.v1.endpoints.inquiries import router_inquiries
from api.v1.endpoints.notifications import router_notifications
from api.v1.endpoints.info import router_info
#--------------------------------
#API 호출
@asynccontextmanager
async def lifespan(app):
    stop = asyncio.Event()
    task = asyncio.create_task(worker(stop)) if flag("WORKER_ENABLED", True) else None
    try:
        yield
    finally:
        stop.set()
        if task:
            await task


app = FastAPI(lifespan=lifespan)


#기능 api 호출
app.include_router(router_dev)
app.include_router(router_login)
app.include_router(router_signup)
app.include_router(router_load_state)
app.include_router(router_logout)
app.include_router(router_email)
app.include_router(router_password)
app.include_router(router_subscribe)
app.include_router(router_account)
app.include_router(router_devices)
app.include_router(router_notices)
app.include_router(router_inquiries)
app.include_router(router_notifications)
app.include_router(router_info)


@app.exception_handler(SQLAlchemyError)
async def database_error(request, error):
    return JSONResponse(status_code=503, content={"detail": "데이터베이스 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."})

#기본 url 들어갈시 표시
@app.post("", include_in_schema=False)
@app.post("/")
def main_page():
    return "Hello! This is the main page of Team-J.H.Y!"


@app.get("/health")
def health():
    return {"status": "ok"}
