from fastapi import FastAPI

from api.v1.endpoints.update_state import router_dev
from api.v1.endpoints.login import router_login
from api.v1.endpoints.signup import router_signup
from api.v1.endpoints.load_state import router_load_state
from api.v1.endpoints.logout import router_logout
from api.v1.endpoints.email_contify import router_email
from api.v1.endpoints.password import router_password
#--------------------------------
#API 호출
app = FastAPI()


#기능 api 호출
app.include_router(router_dev)
app.include_router(router_login)
app.include_router(router_signup)
app.include_router(router_load_state)
app.include_router(router_logout)
app.include_router(router_email)
app.include_router(router_password)

#기본 url 들어갈시 표시
@app.post("")
def main_page():
    return "Hello! This is the main page of Team-J.H.Y!"