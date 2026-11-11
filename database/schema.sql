CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE devices (
    device_id VARCHAR(24) NOT NULL, 
    device_name VARCHAR(24) NOT NULL, 
    PRIMARY KEY (device_id), 
    UNIQUE (device_name)
);

CREATE TABLE email_verification (
    email VARCHAR(255) NOT NULL, 
    purpose VARCHAR(16) NOT NULL, 
    code_hash VARCHAR(64) NOT NULL, 
    expires_at DATETIME(6) NOT NULL, 
    sent_at DATETIME(6) NOT NULL, 
    attempts INTEGER NOT NULL, 
    verified_at DATETIME(6), 
    PRIMARY KEY (email, purpose)
);

CREATE TABLE login_attempt (
    email VARCHAR(255) NOT NULL, 
    failures INTEGER NOT NULL, 
    locked_until DATETIME(6), 
    PRIMARY KEY (email)
);

CREATE TABLE users (
    user_id BINARY(16) NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    name VARCHAR(24) NOT NULL, 
    number VARCHAR(4) NOT NULL, 
    PRIMARY KEY (user_id), 
    UNIQUE (email), 
    UNIQUE (password_hash)
);

CREATE TABLE device_credential (
    device_id VARCHAR(24) NOT NULL, 
    key_hash VARCHAR(64) NOT NULL, 
    PRIMARY KEY (device_id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id)
);

CREATE TABLE device_runtime (
    device_id VARCHAR(24) NOT NULL, 
    unavailable BOOL NOT NULL, 
    unavailable_reason VARCHAR(255), 
    sensor_error VARCHAR(255), 
    door_open BOOL, 
    last_seen_at DATETIME(6), 
    last_measured_at DATETIME(6), 
    cycle_status VARCHAR(16) NOT NULL, 
    expected_seconds INTEGER NOT NULL, 
    PRIMARY KEY (device_id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id)
);

CREATE TABLE drying_cycle (
    id BINARY(16) NOT NULL, 
    device_id VARCHAR(24) NOT NULL, 
    started_at DATETIME(6) NOT NULL, 
    ended_at DATETIME(6), 
    collected_at DATETIME(6), 
    outcome VARCHAR(16), 
    PRIMARY KEY (id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id)
);

CREATE INDEX ix_cycle_device_started ON drying_cycle (device_id, started_at);

CREATE TABLE favorite (
    device_id VARCHAR(24) NOT NULL, 
    user_id BINARY(16) NOT NULL, 
    PRIMARY KEY (device_id, user_id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id)
);

CREATE TABLE inquiry (
    id BINARY(16) NOT NULL, 
    user_id BINARY(16) NOT NULL, 
    device_id VARCHAR(24), 
    error_type VARCHAR(64) NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    content TEXT NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    created_at DATETIME(6) NOT NULL, 
    updated_at DATETIME(6) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_inquiry_status_created ON inquiry (status, created_at);

CREATE TABLE notice (
    id BINARY(16) NOT NULL, 
    author_id BINARY(16), 
    title VARCHAR(200) NOT NULL, 
    content TEXT NOT NULL, 
    pinned BOOL NOT NULL, 
    created_at DATETIME(6) NOT NULL, 
    updated_at DATETIME(6) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(author_id) REFERENCES users (user_id) ON DELETE SET NULL
);

CREATE TABLE push_token (
    token VARCHAR(512) NOT NULL, 
    user_id BINARY(16) NOT NULL, 
    PRIMARY KEY (token), 
    FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE INDEX ix_push_token_user_id ON push_token (user_id);

CREATE TABLE session (
    session_id VARCHAR(255) NOT NULL, 
    user_id BINARY(16) NOT NULL, 
    created_at DATETIME(6) NOT NULL DEFAULT now(), 
    expired_at DATETIME(6) NOT NULL, 
    purpose VARCHAR(16) NOT NULL DEFAULT 'login', 
    password_verified_at DATETIME(6), 
    PRIMARY KEY (session_id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id)
);

CREATE TABLE state (
    device_id VARCHAR(24) NOT NULL, 
    state VARCHAR(9) NOT NULL DEFAULT 'not_used', 
    updated_at DATETIME(6) NOT NULL DEFAULT now(), 
    PRIMARY KEY (device_id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id)
);

CREATE TABLE state_log (
    state_log_id BIGINT NOT NULL AUTO_INCREMENT, 
    device_id VARCHAR(24) NOT NULL, 
    state VARCHAR(15) NOT NULL DEFAULT 'not_used', 
    created_at DATETIME(6) NOT NULL DEFAULT now(), 
    PRIMARY KEY (state_log_id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id)
);

CREATE INDEX ix_state_log_device_time_state ON state_log (device_id, created_at, state);

CREATE TABLE subscribe (
    device_id VARCHAR(24) NOT NULL, 
    user_id BINARY(16) NOT NULL, 
    PRIMARY KEY (device_id, user_id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id)
);

CREATE INDEX ix_subscribe_user_device ON subscribe (user_id, device_id);

CREATE TABLE subscribe_log (
    id BINARY(16) NOT NULL, 
    device_id VARCHAR(24) NOT NULL, 
    user_id BINARY(16) NOT NULL, 
    created_at DATETIME NOT NULL DEFAULT now(), 
    state VARCHAR(15) NOT NULL DEFAULT 'not_subscribed', 
    PRIMARY KEY (id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id)
);

CREATE TABLE telemetry_event (
    device_id VARCHAR(24) NOT NULL, 
    event_id VARCHAR(64) NOT NULL, 
    measured_at DATETIME(6) NOT NULL, 
    received_at DATETIME(6) NOT NULL, 
    payload_hash VARCHAR(64) NOT NULL, 
    payload JSON NOT NULL, 
    PRIMARY KEY (device_id, event_id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id)
);

CREATE TABLE user_profile (
    user_id BINARY(16) NOT NULL, 
    image_url VARCHAR(2048), 
    PRIMARY KEY (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE user_settings (
    user_id BINARY(16) NOT NULL, 
    notifications_enabled BOOL NOT NULL, 
    vibration_enabled BOOL NOT NULL, 
    theme VARCHAR(8) NOT NULL, 
    completed BOOL NOT NULL, 
    paused BOOL NOT NULL, 
    stopped BOOL NOT NULL, 
    uncollected BOOL NOT NULL, 
    PRIMARY KEY (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE cycle_user (
    cycle_id BINARY(16) NOT NULL, 
    user_id BINARY(16) NOT NULL, 
    subscribed_at DATETIME(6) NOT NULL, 
    PRIMARY KEY (cycle_id, user_id), 
    FOREIGN KEY(cycle_id) REFERENCES drying_cycle (id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE notification (
    id BINARY(16) NOT NULL, 
    user_id BINARY(16) NOT NULL, 
    device_id VARCHAR(24) NOT NULL, 
    cycle_id BINARY(16), 
    event_key VARCHAR(128) NOT NULL, 
    kind VARCHAR(16) NOT NULL, 
    message VARCHAR(255) NOT NULL, 
    created_at DATETIME(6) NOT NULL, 
    read_at DATETIME(6), 
    delivered_at DATETIME(6), 
    delivery_attempts INTEGER NOT NULL, 
    next_attempt_at DATETIME(6), 
    PRIMARY KEY (id), 
    FOREIGN KEY(cycle_id) REFERENCES drying_cycle (id), 
    FOREIGN KEY(device_id) REFERENCES devices (device_id), 
    FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
    CONSTRAINT uq_notification_user_event UNIQUE (user_id, event_key)
);

CREATE INDEX ix_notification_user_id ON notification (user_id);

INSERT INTO alembic_version (version_num) VALUES ('0001');

-- Running upgrade 0001 -> 0002

CREATE TABLE push_delivery (
    notification_id BINARY(16) NOT NULL, 
    token VARCHAR(512) NOT NULL, 
    delivered_at DATETIME(6) NOT NULL, 
    PRIMARY KEY (notification_id, token), 
    FOREIGN KEY(notification_id) REFERENCES notification (id) ON DELETE CASCADE, 
    FOREIGN KEY(token) REFERENCES push_token (token) ON DELETE CASCADE
);

ALTER TABLE push_token ADD COLUMN session_id VARCHAR(255);

ALTER TABLE push_token ADD FOREIGN KEY(session_id) REFERENCES session (session_id) ON DELETE CASCADE;

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

-- Running upgrade 0002 -> 0003

ALTER TABLE device_runtime ADD COLUMN last_door_measured_at DATETIME(6);

CREATE INDEX ix_telemetry_device_measured ON telemetry_event (device_id, measured_at);

UPDATE device_runtime SET last_door_measured_at=coalesce((SELECT max(telemetry_event.measured_at) AS max_1 
FROM telemetry_event 
WHERE telemetry_event.device_id = device_runtime.device_id AND telemetry_event.measured_at <= device_runtime.last_measured_at AND CASE JSON_EXTRACT(telemetry_event.payload, '$."door_open"') WHEN 'null' THEN NULL ELSE JSON_UNQUOTE(JSON_EXTRACT(telemetry_event.payload, '$."door_open"')) END IS NOT NULL AND CASE JSON_EXTRACT(telemetry_event.payload, '$."door_open"') WHEN 'null' THEN NULL WHEN true THEN true ELSE false END = device_runtime.door_open), device_runtime.last_measured_at) WHERE device_runtime.door_open IS NOT NULL;

UPDATE device_runtime SET last_measured_at=(SELECT state.updated_at 
FROM state 
WHERE state.device_id = device_runtime.device_id AND (EXISTS (SELECT 1 
FROM telemetry_event 
WHERE telemetry_event.device_id = state.device_id AND telemetry_event.measured_at = state.updated_at AND CASE JSON_EXTRACT(telemetry_event.payload, '$."state"') WHEN 'null' THEN NULL ELSE JSON_UNQUOTE(JSON_EXTRACT(telemetry_event.payload, '$."state"')) END IS NOT NULL))) WHERE device_runtime.last_measured_at IS NOT NULL;

UPDATE alembic_version SET version_num='0003' WHERE alembic_version.version_num = '0002';

