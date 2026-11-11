# 실제 MySQL 스키마

검증 대상: 로컬 jhy_development. 데이터 행이나 자격 증명은 포함하지 않습니다. 마이그레이션 버전 테이블을 제외한 22개 테이블이며 기존 8개와 추가 14개로 구성됩니다.

보류 기능 제거 이후에도 `favorite` 테이블과 `device_runtime.door_open`, `device_runtime.last_door_measured_at`, `drying_cycle.collected_at`, `user_settings.uncollected` 컬럼은 기존 데이터 보존을 위해 유지합니다. 과거 미수거 알림 행도 DB에 남으며 API 조회와 발송 대상에서 제외됩니다.

## cycle_user

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| cycle_id | BINARY(16) | 불가 | 없음 | O |
| user_id | BINARY(16) | 불가 | 없음 | O |
| subscribed_at | DATETIME | 불가 | 없음 |  |

- FK: `cycle_id` → `drying_cycle.id`; {}
- FK: `user_id` → `users.user_id`; {'ondelete': 'CASCADE'}
- INDEX `user_id`: `user_id`

## device_credential

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| device_id | VARCHAR(24) | 불가 | 없음 | O |
| key_hash | VARCHAR(64) | 불가 | 없음 |  |

- FK: `device_id` → `devices.device_id`; {}

## device_runtime

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| device_id | VARCHAR(24) | 불가 | 없음 | O |
| unavailable | TINYINT | 불가 | 없음 |  |
| unavailable_reason | VARCHAR(255) | 허용 | 없음 |  |
| sensor_error | VARCHAR(255) | 허용 | 없음 |  |
| door_open | TINYINT | 허용 | 없음 |  |
| last_seen_at | DATETIME | 허용 | 없음 |  |
| last_measured_at | DATETIME | 허용 | 없음 |  |
| cycle_status | VARCHAR(16) | 불가 | 없음 |  |
| expected_seconds | INTEGER | 불가 | 없음 |  |
| last_door_measured_at | DATETIME | 허용 | 없음 |  |

- FK: `device_id` → `devices.device_id`; {}

`last_measured_at`은 전류·진동 측정 시각입니다. `last_door_measured_at`은 문 측정 시각입니다. `0003` 마이그레이션은 이전에 저장된 측정과 장치 상태를 사용해 두 시각을 복원합니다.

## devices

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| device_id | VARCHAR(24) | 불가 | 없음 | O |
| device_name | VARCHAR(24) | 불가 | 없음 |  |

- UNIQUE: `device_name`
- INDEX `device_name`: `device_name`

## drying_cycle

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| id | BINARY(16) | 불가 | 없음 | O |
| device_id | VARCHAR(24) | 불가 | 없음 |  |
| started_at | DATETIME | 불가 | 없음 |  |
| ended_at | DATETIME | 허용 | 없음 |  |
| collected_at | DATETIME | 허용 | 없음 |  |
| outcome | VARCHAR(16) | 허용 | 없음 |  |

- FK: `device_id` → `devices.device_id`; {}
- INDEX `ix_cycle_device_started`: `device_id,started_at`

## email_verification

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| email | VARCHAR(255) | 불가 | 없음 | O |
| purpose | VARCHAR(16) | 불가 | 없음 | O |
| code_hash | VARCHAR(64) | 불가 | 없음 |  |
| expires_at | DATETIME | 불가 | 없음 |  |
| sent_at | DATETIME | 불가 | 없음 |  |
| attempts | INTEGER | 불가 | 없음 |  |
| verified_at | DATETIME | 허용 | 없음 |  |


## favorite

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| device_id | VARCHAR(24) | 불가 | 없음 | O |
| user_id | BINARY(16) | 불가 | 없음 | O |

- FK: `device_id` → `devices.device_id`; {}
- FK: `user_id` → `users.user_id`; {}
- INDEX `user_id`: `user_id`

## inquiry

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| id | BINARY(16) | 불가 | 없음 | O |
| user_id | BINARY(16) | 불가 | 없음 |  |
| device_id | VARCHAR(24) | 허용 | 없음 |  |
| error_type | VARCHAR(64) | 불가 | 없음 |  |
| title | VARCHAR(200) | 불가 | 없음 |  |
| content | TEXT | 불가 | 없음 |  |
| status | VARCHAR(16) | 불가 | 없음 |  |
| created_at | DATETIME | 불가 | 없음 |  |
| updated_at | DATETIME | 불가 | 없음 |  |

- FK: `device_id` → `devices.device_id`; {}
- FK: `user_id` → `users.user_id`; {'ondelete': 'CASCADE'}
- INDEX `device_id`: `device_id`
- INDEX `ix_inquiry_status_created`: `status,created_at`
- INDEX `user_id`: `user_id`

## login_attempt

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| email | VARCHAR(255) | 불가 | 없음 | O |
| failures | INTEGER | 불가 | 없음 |  |
| locked_until | DATETIME | 허용 | 없음 |  |


## notice

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| id | BINARY(16) | 불가 | 없음 | O |
| author_id | BINARY(16) | 허용 | 없음 |  |
| title | VARCHAR(200) | 불가 | 없음 |  |
| content | TEXT | 불가 | 없음 |  |
| pinned | TINYINT | 불가 | 없음 |  |
| created_at | DATETIME | 불가 | 없음 |  |
| updated_at | DATETIME | 불가 | 없음 |  |

- FK: `author_id` → `users.user_id`; {'ondelete': 'SET NULL'}
- INDEX `author_id`: `author_id`

## notification

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| id | BINARY(16) | 불가 | 없음 | O |
| user_id | BINARY(16) | 불가 | 없음 |  |
| device_id | VARCHAR(24) | 불가 | 없음 |  |
| cycle_id | BINARY(16) | 허용 | 없음 |  |
| event_key | VARCHAR(128) | 불가 | 없음 |  |
| kind | VARCHAR(16) | 불가 | 없음 |  |
| message | VARCHAR(255) | 불가 | 없음 |  |
| created_at | DATETIME | 불가 | 없음 |  |
| read_at | DATETIME | 허용 | 없음 |  |
| delivered_at | DATETIME | 허용 | 없음 |  |
| delivery_attempts | INTEGER | 불가 | 없음 |  |
| next_attempt_at | DATETIME | 허용 | 없음 |  |

- FK: `cycle_id` → `drying_cycle.id`; {}
- FK: `device_id` → `devices.device_id`; {}
- FK: `user_id` → `users.user_id`; {'ondelete': 'CASCADE'}
- UNIQUE: `user_id,event_key`
- INDEX `cycle_id`: `cycle_id`
- INDEX `device_id`: `device_id`
- INDEX `ix_notification_user_id`: `user_id`
- INDEX `uq_notification_user_event`: `user_id,event_key`

## push_delivery

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| notification_id | BINARY(16) | 불가 | 없음 | O |
| token | VARCHAR(512) | 불가 | 없음 | O |
| delivered_at | DATETIME | 불가 | 없음 |  |

- FK: `notification_id` → `notification.id`; {'ondelete': 'CASCADE'}
- FK: `token` → `push_token.token`; {'ondelete': 'CASCADE'}
- INDEX `token`: `token`

## push_token

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| token | VARCHAR(512) | 불가 | 없음 | O |
| user_id | BINARY(16) | 불가 | 없음 |  |
| session_id | VARCHAR(255) | 허용 | 없음 |  |

- FK: `user_id` → `users.user_id`; {'ondelete': 'CASCADE'}
- FK: `session_id` → `session.session_id`; {'ondelete': 'CASCADE'}
- INDEX `ix_push_token_user_id`: `user_id`
- INDEX `session_id`: `session_id`

## session

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| session_id | VARCHAR(255) | 불가 | 없음 | O |
| user_id | BINARY(16) | 불가 | 없음 |  |
| created_at | DATETIME | 불가 | (now()) |  |
| expired_at | DATETIME | 불가 | 없음 |  |
| purpose | VARCHAR(16) | 불가 | 'login' |  |
| password_verified_at | DATETIME | 허용 | 없음 |  |

- FK: `user_id` → `users.user_id`; {}
- INDEX `user_id`: `user_id`

## state

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| device_id | VARCHAR(24) | 불가 | 없음 | O |
| state | VARCHAR(9) | 불가 | 'not_used' |  |
| updated_at | DATETIME | 불가 | (now()) |  |

- FK: `device_id` → `devices.device_id`; {}

## state_log

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| state_log_id | BIGINT | 불가 | 없음 | O |
| device_id | VARCHAR(24) | 불가 | 없음 |  |
| state | VARCHAR(15) | 불가 | 'not_used' |  |
| created_at | DATETIME | 불가 | (now()) |  |

- FK: `device_id` → `devices.device_id`; {}
- INDEX `ix_state_log_device_time_state`: `device_id,created_at,state`

## subscribe

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| device_id | VARCHAR(24) | 불가 | 없음 | O |
| user_id | BINARY(16) | 불가 | 없음 | O |

- FK: `device_id` → `devices.device_id`; {}
- FK: `user_id` → `users.user_id`; {}
- INDEX `ix_subscribe_user_device`: `user_id,device_id`

## subscribe_log

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| id | BINARY(16) | 불가 | 없음 | O |
| device_id | VARCHAR(24) | 불가 | 없음 |  |
| user_id | BINARY(16) | 불가 | 없음 |  |
| created_at | DATETIME | 불가 | (now()) |  |
| state | VARCHAR(15) | 불가 | 'not_subscribed' |  |

- FK: `device_id` → `devices.device_id`; {}
- FK: `user_id` → `users.user_id`; {}
- INDEX `device_id`: `device_id`
- INDEX `user_id`: `user_id`

## telemetry_event

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| device_id | VARCHAR(24) | 불가 | 없음 | O |
| event_id | VARCHAR(64) | 불가 | 없음 | O |
| measured_at | DATETIME | 불가 | 없음 |  |
| received_at | DATETIME | 불가 | 없음 |  |
| payload_hash | VARCHAR(64) | 불가 | 없음 |  |
| payload | JSON | 불가 | 없음 |  |

- FK: `device_id` → `devices.device_id`; {}
- INDEX `ix_telemetry_device_measured`: `device_id, measured_at`

## user_profile

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| user_id | BINARY(16) | 불가 | 없음 | O |
| image_url | VARCHAR(2048) | 허용 | 없음 |  |

- FK: `user_id` → `users.user_id`; {'ondelete': 'CASCADE'}

## user_settings

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| user_id | BINARY(16) | 불가 | 없음 | O |
| notifications_enabled | TINYINT | 불가 | 없음 |  |
| vibration_enabled | TINYINT | 불가 | 없음 |  |
| theme | VARCHAR(8) | 불가 | 없음 |  |
| completed | TINYINT | 불가 | 없음 |  |
| paused | TINYINT | 불가 | 없음 |  |
| stopped | TINYINT | 불가 | 없음 |  |
| uncollected | TINYINT | 불가 | 없음 |  |

- FK: `user_id` → `users.user_id`; {'ondelete': 'CASCADE'}

## users

| 컬럼 | 타입 | NULL | DB 기본값 | PK |
|---|---|---|---|---|
| user_id | BINARY(16) | 불가 | 없음 | O |
| email | VARCHAR(255) | 불가 | 없음 |  |
| password_hash | VARCHAR(255) | 불가 | 없음 |  |
| name | VARCHAR(24) | 불가 | 없음 |  |
| number | VARCHAR(4) | 불가 | 없음 |  |

- UNIQUE: `email`
- UNIQUE: `password_hash`
- INDEX `email`: `email`
- INDEX `password_hash`: `password_hash`
