from datetime import timedelta
import json
from pathlib import Path
import re

import pytest
from sqlalchemy import select

from conftest import PASSWORD, login
from main import app
from models.account import Email_Verification, Login_Attempt
from models.session_model import Session_Model
from models.users import Users
from services.common import utcnow


def code_from(messages):
    return re.search(r"[0-9]{6}", messages[-1].get_content()).group()


def test_active_notion_contract_is_preserved():
    contract = json.loads((Path(__file__).parents[1] / "docs/notion-api-contract.json").read_text(encoding="utf-8"))
    paths = app.openapi()["paths"]
    assert all(path.startswith("/") for path in paths)
    for endpoint in contract:
        exposed = endpoint["method"].lower() in paths.get(endpoint["path"], {})
        assert exposed is not endpoint.get("retired", False)
    assert paths["/api/v1/users/me"]["get"]["security"] == [{"SessionCookie": []}]
    assert paths["/api/v1/state/{device_id}"]["patch"]["security"] == [{"DeviceKey": []}]


def test_login_completes_within_documented_budget(client, users):
    import time
    started = time.perf_counter()
    login(client)
    assert time.perf_counter() - started < 2.0


def test_signup_verification_and_uuid(client, db, fake_smtp):
    data = {"email": "new@example.com", "password": PASSWORD, "name": "새사용자", "number": "1234"}
    assert client.post("/api/v1/users/signup", json=data).status_code == 403
    assert client.post("/api/v1/signup/email", json={"email": data["email"]}).json() == {"success": True}
    code = code_from(fake_smtp)
    check = client.post("/api/v1/check/email_code", json={"email": data["email"], "code": code})
    assert check.json() == {"success": True, "massage": "인증 성공"}
    assert client.post("/api/v1/check/email_code", json={"email": data["email"], "code": code}).json()["success"] is False
    response = client.post("/api/v1/users/signup", json=data)
    assert response.json() == {"success": True, "message": "회원가입이 완료되었습니다."}
    user = db.scalar(select(Users).where(Users.email == data["email"]))
    assert len(user.user_id) == 16
    assert user.password_hash != PASSWORD
    assert client.post("/api/v1/users/signup", json=data).status_code == 409
    assert client.post("/api/v1/users/login", json={"email": data["email"], "password": PASSWORD}).status_code == 200


@pytest.mark.parametrize("change", [{"email": "bad"}, {"password": "short"}, {"number": "12345"},
                                    {"name": " "}, {"password_confirm": "different"}])
def test_signup_invalid_input(client, change):
    data = {"email": "new@example.com", "password": PASSWORD, "name": "사용자", "number": "1234", **change}
    assert client.post("/api/v1/users/signup", json=data).status_code == 422


def test_email_failures_throttle_expiry_and_attempt_limit(client, db, fake_smtp):
    email = "new@example.com"
    payload = {"email": email}
    client.post("/api/v1/signup/email", json=payload)
    assert client.post("/api/v1/signup/email", json=payload).status_code == 429
    code = code_from(fake_smtp)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert client.post("/api/v1/check/email_code", json={"email": email, "code": wrong}).json()["success"] is False
    assert client.post("/api/v1/check/email_code", json={"email": email, "code": code}).json()["success"] is False
    row = db.get(Email_Verification, (email, "signup"))
    row.expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    result = client.post("/api/v1/check/email_code", json={"email": email, "code": code})
    assert result.json()["massage"] == "시간 초과"


def test_smtp_failure_is_safe(client, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("sensitive provider error")
    monkeypatch.setattr("auth.auth_email.smtplib.SMTP_SSL", fail)
    response = client.post("/api/v1/signup/email", json={"email": "new@example.com"})
    assert response.status_code == 503
    assert "sensitive" not in response.text


def test_login_session_cookie_logout(client, users, db):
    result = login(client)
    assert result.json() == {"message": "로그인 성공", "is_admin": False}
    cookie = result.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Max-Age=86400" in cookie and "SameSite=lax" in cookie
    token = client.cookies.get("session_id")
    assert client.get("/api/v1/users/me").json()["email"] == users[0].email
    assert client.post("/api/v1/logout").json() == {"message": "로그아웃되었습니다."}
    assert db.get(Session_Model, token) is None
    assert client.get("/api/v1/users/me").status_code == 401


def test_expired_and_legacy_sessions(client, users, db):
    login(client)
    token = client.cookies.get("session_id")
    client.cookies.clear()
    client.cookies.set("Session_id", token)
    assert client.get("/api/v1/users/me").status_code == 200
    session = db.get(Session_Model, token)
    session.expired_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/v1/users/me").status_code == 401
    assert db.get(Session_Model, token) is None


def test_login_bad_credentials_lock_and_release(client, users, db):
    for _ in range(10):
        response = client.post("/api/v1/users/login", json={"email": users[0].email, "password": "bad"})
        assert response.status_code == 401
    assert client.post("/api/v1/users/login", json={"email": users[0].email, "password": PASSWORD}).status_code == 429
    row = db.get(Login_Attempt, users[0].email)
    row.locked_until = utcnow() - timedelta(seconds=1)
    db.commit()
    login(client)
    assert db.get(Login_Attempt, users[0].email).failures == 0


def test_password_change_requires_proof_and_revokes_sessions(client, users, db):
    login(client)
    assert client.post("/api/v1/change/password", json={"password": "NewPassword-123"}).status_code == 403
    assert client.post("/api/v1/change/password_auth", json={"password": "bad"}).json()["success"] is False
    assert client.post("/api/v1/change/password_auth", json={"password": PASSWORD}).json()["success"] is True
    assert client.post("/api/v1/change/password", json={"password": "NewPassword-123"}).json()["message"] == "변경 완료"
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.post("/api/v1/users/login", json={"email": users[0].email, "password": PASSWORD}).status_code == 401
    assert client.post("/api/v1/users/login", json={"email": users[0].email, "password": "NewPassword-123"}).status_code == 200


def test_reset_codes_are_scoped_and_single_use(client, users, db, fake_smtp):
    user = users[0]
    client.post("/api/v1/signup/email", json={"email": "signup-only@example.com"})
    code = code_from(fake_smtp)
    assert client.post("/api/v1/forget/check/email_code", json={"email": "signup-only@example.com", "code": code}).json()["success"] is False
    bad = client.post("/api/v1/forget/password", json={"email": user.email, "name": "틀림", "number": user.number})
    assert bad.json()["success"] is False
    assert client.post("/api/v1/forget/password", json={"email": user.email, "name": user.name, "number": user.number}).json()["success"] is True
    code = code_from(fake_smtp)
    assert client.post("/api/v1/forget/check/email_code", json={"email": user.email, "code": code}).json()["success"] is True
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.post("/api/v1/change/password", json={"password": "Recovered-Password"}).status_code == 200
    assert client.post("/api/v1/forget/check/email_code", json={"email": user.email, "code": code}).json()["success"] is False
    assert client.post("/api/v1/users/login", json={"email": user.email, "password": "Recovered-Password"}).status_code == 200


def test_shared_login_returns_role_and_enforces_admin_access(client, users):
    assert client.get("/api/v1/admin/devices").status_code == 401
    assert login(client).json()["is_admin"] is False
    assert client.get("/api/v1/admin/devices").status_code == 403
    assert login(client, users[2].email).json() == {"message": "로그인 성공", "is_admin": True}
    assert client.get("/api/v1/users/me").json()["is_admin"] is True
    assert client.get("/api/v1/admin/devices").status_code == 200
