# ESP32·앱 연동 계약

`PATCH /api/v1/state/{device_id}`로 장치 상태를 전송합니다. `POST /api/v1/devices/{device_id}/events`는 `event_id`, `measured_at`을 필수로 받아 전송 큐의 중복 재시도를 처리합니다. 장치 등록은 [README](../README.md)의 `add-device` 명령을 사용합니다. 두 API 모두 등록한 장치의 `X-Device-Key` 헤더가 필요합니다.

```http
POST /api/v1/devices/dryer-01/events
Content-Type: application/json
X-Device-Key: <등록한 장치의 키>
```

```json
{
  "event_id": "장치가-생성한-고유-ID",
  "measured_at": "2026-11-07T00:00:00Z",
  "state": "used",
  "Vibration": true,
  "V_Data_before": [0.0, 0.0, 1.0],
  "V_Data_After": [0.3, 0.2, 1.1],
  "Current": true,
  "C_Data": "16.6"
}
```

시각 예시는 형식 설명입니다. 실제 전송에는 측정 시각을 UTC로 넣습니다. 현재보다 5분 넘게 미래인 이벤트는 거부합니다. `PATCH`의 `C_Data`는 0 이상의 유한한 숫자 문자열입니다. `POST /events`는 JSON 숫자도 받아 문자열로 반환하며, 가속도 배열 두 개 대신 0 이상의 유한한 `vibration_hz` 값을 받을 수 있습니다. 가속도 배열은 각각 유한한 숫자 세 개입니다. 기존 코드의 `V_data_before`, `V_data_after`, `C_data` 철자도 호환됩니다.

`state`는 `used`, `not_used`, `paused`, `error`입니다. 사용 중 판정에는 전류·진동 감지 값이 모두 참이어야 합니다. 두 값이 모두 참인 요청을 `not_used`로 보낼 수 없습니다. `POST /events`에서 상태를 생략하면 서버가 두 감지 값으로 사용 여부를 판정합니다. ESP32가 보정한 `Current`와 `Vibration` 값을 전송해야 합니다.

측정 실패는 `POST /events`에 `event_id`, `measured_at`, `state: "error"`, 선택 사항인 `sensor_error`를 보내 기록합니다. 오류 설명만 제공하고 `state`를 생략해도 오류로 처리합니다. 실패한 측정값은 생략할 수 있습니다. 정상 측정이 도착하면 오류 표시를 해제합니다.

같은 장치에서 같은 이벤트 ID·본문을 재전송하면 `200`과 `applied: false`를 반환하고 알림·상태를 다시 생성하지 않습니다. 펌웨어는 `success: true`이면 해당 이벤트를 전송 대기열에서 완료 처리할 수 있습니다. ID는 같고 본문이 다르면 `409`, 장치 키가 틀리면 `401`, 필드 검증에 실패하면 `422`입니다. 늦게 도착한 과거 측정도 `telemetry_event.payload`에 저장합니다. 전류·진동 상태는 최신 측정 시각을 기준으로 갱신합니다. 기존 전류·진동 이벤트 재전송 시 과거에 포함된 `door_open`은 무시합니다.

사용 중 최초 시점부터 `not_used` 전환까지 40분 미만이면 중단, 40분 이상이면 완료입니다. 하트비트와 일시정지 후 재개는 시작 시각을 초기화하지 않습니다. 완료·중단 시 구독자별 알림·사용 기록을 만들고 현재 구독을 해제합니다. 같은 장치를 여러 사용자가 구독할 수 있습니다.

앱은 `/api/v1/devices`의 상태, 통신 오류, 마지막 수신 시각, 추정 남은 시간과 진행률을 사용합니다. 건조가 끝난 장치는 통신이 정상이고 센서 오류와 이용 불가 설정이 없으면 이용 가능으로 표시합니다. 자동 갱신 권장 간격은 `/api/v1/info`의 `poll_interval_seconds`입니다. `/api/v1/notifications/stream`은 로그인 쿠키를 사용하는 SSE이며 완료·일시정지·중단 알림을 전달합니다. 알림 ID로 중복을 제거하고, 앱이 종료된 상태의 푸시는 FCM 설정 및 모바일 클라이언트 구현이 필요합니다.

프로필 이미지, 알림 설정, 문의, 공지, 관리자 API의 정확한 JSON 스키마와 인증 요구사항은 실행 중인 `/docs` 또는 `docs/openapi.json`을 기준으로 사용합니다. 관리자와 일반 사용자는 `POST /api/v1/users/login`으로 로그인합니다. 허용 목록에 포함된 계정은 응답의 `is_admin`이 `true`이며 로그인 세션으로 관리자 API를 호출할 수 있습니다.
