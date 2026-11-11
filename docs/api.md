# API 참조

OpenAPI에는 HTTP 경로 41개와 작업 50개가 있습니다. 기존 Notion 계약 중 보류된 즐겨찾기 추가를 제외한 14개 작업을 제공합니다.

로그인 API를 실행하면 HttpOnly session_id 쿠키가 설정됩니다. Swagger도 로그인 후 같은 브라우저의 쿠키를 사용합니다. 장치 전송은 Swagger Authorize의 DeviceKey에 장치 키를 입력하거나 X-Device-Key 헤더로 인증합니다. 관리자는 검증된 계정의 이메일이 ADMIN_EMAILS에 포함되어야 합니다.

공통 로그인 `POST /api/v1/users/login`에 `email`과 `password`를 보냅니다. 성공 응답에는 기존 `message`와 권한을 구분하는 `is_admin`이 포함됩니다. `is_admin`은 관리자에게 `true`, 일반 사용자에게 `false`입니다. 서버는 각 관리자 API 요청에서 세션과 권한을 확인합니다.

| 메서드 | 경로 | 인증 |
|---|---|---|
| PATCH | `/api/v1/state/{device_id}` | 장치 키 |
| GET | `/api/v1/state/{device_id}` | 공개 |
| POST | `/api/v1/devices/{device_id}/events` | 장치 키 |
| POST | `/api/v1/users/login` | 이메일·비밀번호 공통 로그인 |
| POST | `/api/v1/users/signup` | 공개 |
| GET | `/api/v1/state/all` | 공개 |
| POST | `/api/v1/logout` | 사용자 세션 |
| POST | `/api/v1/signup/email` | 공개 |
| POST | `/api/v1/check/email_code` | 공개 |
| POST | `/api/v1/forget/password` | 공개 |
| POST | `/api/v1/forget/check/email_code` | 공개 |
| POST | `/api/v1/change/password_auth` | 사용자 세션 |
| POST | `/api/v1/change/password` | 사용자 세션 |
| POST | `/api/v1/subscribe/add` | 사용자 세션 |
| DELETE | `/api/v1/subscribe/delete` | 사용자 세션 |
| DELETE | `/api/v1/subscribe/delete/{device_name}` | 사용자 세션 |
| GET | `/api/v1/users/me` | 사용자 세션 |
| DELETE | `/api/v1/users/me` | 사용자 세션 |
| PATCH | `/api/v1/users/me` | 사용자 세션 |
| GET | `/api/v1/users/me/image` | 사용자 세션 |
| PUT | `/api/v1/users/me/image` | 사용자 세션 |
| GET | `/api/v1/users/me/settings` | 사용자 세션 |
| PATCH | `/api/v1/users/me/settings` | 사용자 세션 |
| GET | `/api/v1/devices` | 공개 |
| GET | `/api/v1/devices/{device_id}` | 공개 |
| GET | `/api/v1/users/me/history` | 사용자 세션 |
| GET | `/api/v1/users/me/history/{cycle_id}` | 사용자 세션 |
| GET | `/api/v1/admin/devices` | 관리자 세션 |
| GET | `/api/v1/admin/devices/{device_id}` | 관리자 세션 |
| PATCH | `/api/v1/admin/devices/{device_id}/availability` | 관리자 세션 |
| GET | `/api/v1/admin/devices/{device_id}/history` | 관리자 세션 |
| GET | `/api/v1/notices` | 공개 |
| GET | `/api/v1/admin/notices` | 관리자 세션 |
| POST | `/api/v1/admin/notices` | 관리자 세션 |
| GET | `/api/v1/notices/{notice_id}` | 공개 |
| PATCH | `/api/v1/admin/notices/{notice_id}` | 관리자 세션 |
| DELETE | `/api/v1/admin/notices/{notice_id}` | 관리자 세션 |
| POST | `/api/v1/inquiries` | 사용자 세션 |
| GET | `/api/v1/inquiries` | 사용자 세션 |
| GET | `/api/v1/admin/inquiries` | 관리자 세션 |
| GET | `/api/v1/admin/inquiries/{inquiry_id}` | 관리자 세션 |
| PATCH | `/api/v1/admin/inquiries/{inquiry_id}/status` | 관리자 세션 |
| GET | `/api/v1/notifications` | 사용자 세션 |
| GET | `/api/v1/notifications/stream` | 사용자 세션 |
| PATCH | `/api/v1/notifications/{notification_id}/read` | 사용자 세션 |
| POST | `/api/v1/users/me/push-tokens` | 사용자 세션 |
| DELETE | `/api/v1/users/me/push-tokens` | 사용자 세션 |
| GET | `/api/v1/info` | 공개 |
| POST | `/` | 공개 |
| GET | `/health` | 공개 |

## 공통 동작

- 이메일 코드 확인 응답의 `massage` 키는 기존 명세와 호환됩니다.
- 목록 API는 데이터가 없으면 빈 배열을 반환합니다. 리소스 부재는 404, 잘못된 입력은 422, 인증은 401, 권한은 403, 충돌은 409, 제한은 429, DB·SMTP 일시 오류는 503입니다.
- 새 리소스의 ID는 UUID 문자열이고 날짜는 UTC ISO 8601입니다. 비밀번호 해시·세션 토큰·장치 키는 조회 응답에 포함하지 않습니다.
- 공지·문의·알림·사용 기록 목록은 limit(1~100)과 offset(0 이상)을 지원합니다. 장치 목록은 q, state, available을 지원합니다.
- 장치 목록은 장치 ID순으로 표시합니다. 완료·중단 상태인 장치는 통신이 정상이고 센서 오류와 이용 불가 설정이 없으면 이용 가능으로 표시합니다.
- 알림 설정과 내역, 실시간 스트림, 푸시에는 완료(`completed`), 일시정지(`paused`), 중단(`stopped`)이 적용됩니다.
- 신규 비밀번호는 8~128자입니다. password_confirm은 호환성을 위해 선택 값이며 제출 시 일치를 확인합니다. 학번은 기존 DB에 맞춰 숫자 네 자리, 이름은 1~24자입니다.
- 문의는 device_id가 선택 값이고 error_type과 content가 필수입니다. title은 선택 값으로 미지정 시 error_type을 제목으로 사용합니다.
- 문의 상태는 unread(미확인), reviewing(확인 중), resolved(처리 완료)입니다. 공지는 pinned=true 항목을 상단에 표시합니다.
- 프로필 이미지는 JPEG/PNG/WEBP, 5MB·천만 픽셀 이하로 받고 1024px 이하 PNG로 재인코딩합니다. 다른 계정이나 비로그인 사용자는 프로필 이미지 조회 API에 접근할 수 없습니다.
- 푸시 토큰은 등록한 로그인 세션에 연결됩니다. 로그아웃이나 비밀번호 변경 후 해당 토큰으로 새 알림을 보내지 않습니다. 푸시는 재시도가 가능한 전달이며 클라이언트는 notification_id로 중복을 제거해야 합니다.

요청 본문의 필수 필드와 세부 제한은 openapi.json 또는 실행 중인 /docs에서 확인합니다. 센서 전송 예시는 device-integration.md에 있습니다.
