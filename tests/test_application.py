from datetime import timedelta
from io import BytesIO

from PIL import Image
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from conftest import PASSWORD, login, report, telemetry
from database.connection import Create_db
from main import app
from models.favorite import Favorite
from models.inquiry import Inquiry
from models.notification import Notification, Push_Token
from models.session_model import Session_Model
from models.state import State
from models.users import Users
from services.common import iso, uid, utcnow
from services.notifications import deliver_pending


def test_sse_stream_delivers_user_notification(client, users, device, db, monkeypatch):
    import asyncio
    from contextlib import nullcontext
    from starlette.requests import Request
    from api.v1.endpoints.notifications import notification_stream
    login(client)
    now = utcnow()
    db.add_all([
        Notification(user_id=users[0].user_id, device_id=device.device_id, kind="uncollected",
                     event_key="legacy-sse", message="미수거 알림", created_at=now - timedelta(seconds=1)),
        Notification(user_id=users[0].user_id, device_id=device.device_id, kind="stopped",
                     event_key="sse-test", message="SSE 알림", created_at=now),
    ])
    db.commit()
    monkeypatch.setattr("api.v1.endpoints.notifications.SessionLocal", lambda: nullcontext(db))
    token = client.cookies.get("session_id")
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    request = Request({"type": "http", "headers": [(b"cookie", ("session_id=" + token).encode())]}, receive)
    response = notification_stream(request, db=db, user=users[0])
    async def first_event():
        try:
            return await response.body_iterator.__anext__()
        finally:
            await response.body_iterator.aclose()
    event = asyncio.run(first_event())
    assert "event: notification" in event and "SSE 알림" in event and token not in event


def test_notice_crud_pinning_and_admin_authorization(client, users):
    data = {"title": "점검 공지", "content": "점검합니다.", "pinned": False}
    assert client.post("/api/v1/admin/notices", json=data).status_code == 401
    login(client)
    assert client.post("/api/v1/admin/notices", json=data).status_code == 403
    client.cookies.clear()
    login(client, "admin@example.com")
    first = client.post("/api/v1/admin/notices", json=data).json()
    pinned = client.post("/api/v1/admin/notices", json={**data, "title": "중요", "pinned": True}).json()
    assert client.get("/api/v1/notices").json()[0]["id"] == pinned["id"]
    url = "/api/v1/admin/notices/" + first["id"]
    assert client.patch(url, json={"content": "수정되었습니다."}).json()["content"] == "수정되었습니다."
    assert client.get("/api/v1/notices/" + first["id"]).status_code == 200
    assert client.post("/api/v1/admin/notices", json={**data, "title": " "}).status_code == 422
    assert client.delete(url).json()["success"] is True
    assert client.get("/api/v1/notices/" + first["id"]).status_code == 404


def test_inquiry_privacy_admin_filters_and_status(client, device, users):
    login(client)
    data = {"device_id": "dryer-01", "error_type": "센서 오류", "title": "확인 요청", "content": "장치 상태를 확인해 주세요."}
    created = client.post("/api/v1/inquiries", json=data)
    assert created.status_code == 200
    inquiry_id = created.json()["id"]
    assert client.get("/api/v1/inquiries").json()[0]["id"] == inquiry_id
    client.cookies.clear()
    login(client, "second@example.com")
    assert client.get("/api/v1/inquiries").json() == []
    client.cookies.clear()
    login(client, "admin@example.com")
    items = client.get("/api/v1/admin/inquiries?status=unread&device_id=dryer-01").json()
    assert items[0]["reporter"]["name"] == users[0].name
    assert client.get("/api/v1/admin/inquiries/" + inquiry_id).status_code == 200
    assert client.patch("/api/v1/admin/inquiries/" + inquiry_id + "/status", json={"status": "resolved"}).json()["status"] == "resolved"
    assert client.get("/api/v1/admin/inquiries?status=unread").json() == []
    assert client.patch("/api/v1/admin/inquiries/" + inquiry_id + "/status", json={"status": "invalid"}).status_code == 422
    assert client.post("/api/v1/inquiries", json={**data, "device_id": "missing"}).status_code == 404
    without_title = {key: value for key, value in data.items() if key != "title"}
    assert client.post("/api/v1/inquiries", json=without_title).status_code == 200


def test_profile_settings_and_private_image_upload(client, users, monkeypatch, tmp_path):
    monkeypatch.setattr("api.v1.endpoints.account.UPLOADS", tmp_path)
    login(client)
    before = client.get("/api/v1/users/me").json()
    assert "password_hash" not in before
    assert client.patch("/api/v1/users/me", json={"name": "새 이름", "number": "2345"}).json()["number"] == "2345"
    assert client.patch("/api/v1/users/me", json={"number": "123456"}).status_code == 422
    settings = client.patch("/api/v1/users/me/settings", json={"theme": "dark", "vibration_enabled": False}).json()
    assert settings["theme"] == "dark" and settings["vibration_enabled"] is False
    assert "uncollected" not in settings
    assert client.get("/api/v1/users/me/settings").json() == settings
    assert client.patch("/api/v1/users/me/settings", json={"theme": "invalid"}).status_code == 422
    image = BytesIO()
    Image.new("RGB", (10, 10), "red").save(image, "PNG")
    result = client.put("/api/v1/users/me/image", files={"file": ("test.png", image.getvalue(), "image/png")})
    assert result.status_code == 200
    assert client.get("/api/v1/users/me/image").headers["content-type"] == "image/png"
    assert client.put("/api/v1/users/me/image", files={"file": ("fake.png", b"not-an-image", "image/png")}).status_code == 422
    client.cookies.clear()
    assert client.get("/api/v1/users/me/image").status_code == 401


def test_account_deletion_cleans_references_and_sessions(client, users, device, db, monkeypatch, tmp_path):
    monkeypatch.setattr("api.v1.endpoints.account.UPLOADS", tmp_path)
    login(client)
    user_id = users[0].user_id
    client.patch("/api/v1/users/me/settings", json={"theme": "dark"})
    db.add(Favorite(device_id=device.device_id, user_id=user_id))
    db.commit()
    client.post("/api/v1/users/me/push-tokens", json={"token": "disposable-test-token"})
    client.post("/api/v1/inquiries", json={"title": "문의", "content": "내용", "error_type": "기타"})
    report(client, telemetry())
    client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"})
    assert client.request("DELETE", "/api/v1/users/me", json={"password": "wrong"}).status_code == 403
    result = client.request("DELETE", "/api/v1/users/me", json={"password": PASSWORD})
    assert result.status_code == 200
    assert db.get(Users, user_id) is None
    assert db.scalar(select(Favorite).where(Favorite.user_id == user_id)) is None
    assert db.scalar(select(func.count()).select_from(Session_Model).where(Session_Model.user_id == user_id)) == 0
    assert db.scalar(select(func.count()).select_from(Inquiry).where(Inquiry.user_id == user_id)) == 0
    assert db.get(State, "dryer-01") is not None
    assert client.get("/api/v1/users/me").status_code == 401


def test_notification_ownership_read_and_push_registration(client, users, device, db, monkeypatch):
    now = utcnow()
    report(client, telemetry(measured_at=iso(now - timedelta(minutes=45))))
    login(client)
    client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"})
    assert client.post("/api/v1/users/me/push-tokens", json={"token": "test-token"}).json()["success"] is True
    report(client, telemetry("not_used", measured_at=iso(now)))
    legacy = Notification(user_id=users[0].user_id, device_id=device.device_id, kind="uncollected",
                          event_key="legacy-push", message="미수거 알림", created_at=now)
    db.add(legacy)
    db.commit()
    rows = client.get("/api/v1/notifications?unread=true").json()
    assert [row["kind"] for row in rows] == ["completed"]
    row = rows[0]
    assert client.patch(f"/api/v1/notifications/{uid(legacy.id)}/read").status_code == 404
    calls = []
    monkeypatch.setenv("FCM_PROJECT_ID", "mock-project")
    monkeypatch.setattr("services.notifications.send_push", lambda token, item: calls.append((token, item.kind)) or "sent")
    deliver_pending(db)
    assert calls == [("test-token", "completed")]
    db.refresh(legacy)
    assert legacy.delivery_attempts == 0 and legacy.delivered_at is None
    client.cookies.clear()
    login(client, "second@example.com")
    assert client.patch("/api/v1/notifications/" + row["id"] + "/read").status_code == 404
    assert client.post("/api/v1/users/me/push-tokens", json={"token": "test-token"}).status_code == 409
    client.cookies.clear()
    login(client)
    assert client.patch("/api/v1/notifications/" + row["id"] + "/read").json()["read"] is True
    assert client.get("/api/v1/notifications?unread=true").json() == []
    assert client.request("DELETE", "/api/v1/users/me/push-tokens", json={"token": "test-token"}).json()["success"] is True


def test_logout_removes_push_tokens_for_that_session(client, users, db):
    login(client)
    client.post("/api/v1/users/me/push-tokens", json={"token": "logout-test-token"})
    assert db.get(Push_Token, "logout-test-token") is not None
    client.post("/api/v1/logout")
    assert db.get(Push_Token, "logout-test-token") is None


def test_push_queue_skips_notifications_without_recipients(client, users, device, db, monkeypatch):
    now = utcnow()
    for index in range(25):
        db.add(Notification(user_id=users[0].user_id, device_id=device.device_id, kind="stopped",
                            event_key="no-token-" + str(index), message="알림", created_at=now - timedelta(minutes=1)))
    row = Notification(user_id=users[1].user_id, device_id=device.device_id, kind="stopped",
                       event_key="deliverable", message="알림", created_at=now)
    db.add_all([row, Push_Token(user_id=users[1].user_id, token="eligible-token")])
    db.commit()
    calls = []
    monkeypatch.setenv("FCM_PROJECT_ID", "mock-project")
    monkeypatch.setattr("services.notifications.send_push", lambda token, row: calls.append(token) or "sent")
    deliver_pending(db)
    assert calls == ["eligible-token"]
    assert row.delivered_at is not None


def test_push_retry_does_not_resend_successful_devices(client, users, device, db, monkeypatch):
    row = Notification(user_id=users[0].user_id, device_id=device.device_id, kind="stopped",
                       event_key="two-phones", message="알림", created_at=utcnow())
    db.add_all([row, Push_Token(user_id=users[0].user_id, token="phone-a"),
                Push_Token(user_id=users[0].user_id, token="phone-b")])
    db.commit()
    calls = []
    failures = {"phone-b"}
    monkeypatch.setenv("FCM_PROJECT_ID", "mock-project")
    def send(token, row):
        calls.append(token)
        if token in failures:
            raise RuntimeError("temporary failure")
        return "sent"
    monkeypatch.setattr("services.notifications.send_push", send)
    deliver_pending(db)
    failures.clear()
    row.next_attempt_at = utcnow() - timedelta(seconds=1)
    db.commit()
    deliver_pending(db)
    assert calls.count("phone-a") == 1 and calls.count("phone-b") == 2
    assert row.delivered_at is not None


def test_push_delivery_retry_and_disabled_provider(client, users, device, db, monkeypatch):
    now = utcnow()
    row = Notification(user_id=users[0].user_id, device_id=device.device_id, kind="stopped",
                       event_key="push-test", message="테스트 알림", created_at=now)
    db.add_all([row, Push_Token(user_id=users[0].user_id, token="mock-token")])
    db.commit()
    calls = []
    monkeypatch.setattr("services.notifications.send_push", lambda token, row: calls.append(token) or "sent")
    deliver_pending(db)
    assert calls == []
    monkeypatch.setenv("FCM_PROJECT_ID", "mock-project")
    def fail(token, row):
        raise RuntimeError("mock provider failure")
    monkeypatch.setattr("services.notifications.send_push", fail)
    deliver_pending(db)
    assert row.delivery_attempts == 1 and row.delivered_at is None and row.next_attempt_at > now
    row.next_attempt_at = now - timedelta(seconds=1)
    db.commit()
    monkeypatch.setattr("services.notifications.send_push", lambda token, row: calls.append(token) or "sent")
    deliver_pending(db)
    assert calls == ["mock-token"] and row.delivered_at is not None


def test_foreign_keys_are_enforced(db):
    db.add(State(device_id="missing-device", state="used", updated_at=utcnow()))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_database_error_is_sanitized(client):
    def failed_db():
        raise OperationalError("SELECT secret", {"password": "do-not-expose"}, Exception("private-error"))
    app.dependency_overrides[Create_db] = failed_db
    response = client.get("/api/v1/state/all")
    assert response.status_code == 503
    assert "secret" not in response.text and "do-not-expose" not in response.text


def test_health_info_and_empty_lists(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/v1/info").json()["push_configured"] is False
    assert client.get("/api/v1/notices").json() == []
    assert client.get("/api/v1/devices").json() == []


def test_removed_features_have_no_routes_or_request_fields(client):
    paths = client.get("/openapi.json").json()
    for method, path in (
        ("POST", "/faverite"),
        ("GET", "/favorites"),
        ("POST", "/favorites"),
        ("DELETE", "/favorites/{device_id}"),
        ("POST", "/devices/{device_id}/door"),
        ("POST", "/devices/{device_id}/collect"),
        ("GET", "/guide"),
        ("GET", "/subscribe"),
        ("GET", "/inquiries/{inquiry_id}"),
        ("POST", "/admin/login"),
    ):
        route = "/api/v1" + path
        assert route not in paths["paths"]
        url = route.format(device_id="dryer-01", inquiry_id="00000000-0000-0000-0000-000000000001")
        assert client.request(method, url).status_code == 404
    schemas = paths["components"]["schemas"]
    assert "door_open" not in schemas["TelemetryData"]["properties"]
    assert "door_open" not in schemas["Device_State"]["properties"]
    assert "uncollected" not in schemas["SettingsPatch"]["properties"]
