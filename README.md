# J.H.Y FastAPI 백엔드

Notion API 명세의 기존 경로와 성공 응답을 유지하고, 기능명세에 필요한 사용자·장치·관리자 API를 추가했습니다. 소스와 설계 근거, 기능별 검증 범위는 [작업 보고서](docs/implementation-report.md)와 [기능 대조표](docs/feature-matrix.md)에 기록합니다.

## 현재 개발 환경

- Python 3.13.17, FastAPI, SQLAlchemy 2, PyMySQL, Argon2, Alembic
- API: `http://127.0.0.1:8000`, Swagger: `http://127.0.0.1:8000/docs`
- MySQL 8.4.13: `127.0.0.1:3307`, DB `jhy_development`
- Workbench 연결: `JHY Local Development`, 사용자 `jhy_app`
- 앱 연결 정보: `.env.local`; 기존 `.env`는 보존했습니다.
- 서버 데이터·관리용 자격 증명·장치 키는 Git에서 제외한 `.local/`에 있습니다.

## 실행과 중지

프로젝트 루트의 PowerShell에서 실행합니다.

```powershell
.\scripts\run.ps1 start
```

프로젝트 전용 MySQL을 시작하고 `.env.local`을 읽어 API를 실행합니다. API는 `Ctrl+C`로 중지합니다. 두 프로세스 모두 이 컴퓨터의 로컬 주소만 사용합니다.

같은 네트워크의 ESP32에서 접근할 때는 API를 실행할 PC의 LAN IP를 지정합니다. 아래 주소를 실제 LAN IP로 바꾸면 ESP32가 `http://<서버 LAN IP>:8000`에 요청할 수 있습니다.

```powershell
.\scripts\run.ps1 start -ListenAddress 192.168.1.10
.\scripts\run.ps1 status -ListenAddress 192.168.1.10
```

```powershell
.\scripts\run.ps1 status
.\.venv\Scripts\python.exe scripts\local_mysql.py stop
```

첫 명령은 API와 MySQL 상태를 확인합니다. 두 번째 명령은 이 프로젝트의 MySQL만 종료하며 데이터를 보존합니다. 이후 `run.ps1 start`가 다시 시작합니다.

새 체크아웃에서 Python 3.13을 설치한 후 환경을 준비할 때는 다음 순서로 실행합니다.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\local_mysql.py setup
$env:JHY_ENV_FILE = (Resolve-Path .env.local).Path
.\.venv\Scripts\python.exe scripts\db.py migrate
```

`setup`은 Oracle ZIP을 검증하고 프로젝트 안에 개발 인스턴스와 임의 비밀번호를 만듭니다. 기존 데이터 디렉터리가 있으면 초기화하지 않습니다. `migrate`는 버전 관리되지 않은 기존 테이블이 있는 DB에 초기 스키마를 덮어쓰지 않습니다. 일반 앱 계정에는 DDL 권한을 주지 않았으며 로컬 마이그레이션 도구가 별도 관리 자격 증명을 사용합니다.

## 계정과 장치

회원가입 순서는 이메일 요청 → 코드 확인 → 회원가입 → 로그인입니다. 이메일 코드 확인의 `massage` 응답 키는 기존 명세와 호환됩니다.

관리자와 일반 사용자는 같은 `POST /api/v1/users/login`을 사용합니다. 응답의 `is_admin`이 `true`이면 관리자입니다.

관리자는 이메일 인증을 거쳐 가입한 실제 계정만 지정할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe scripts\manage.py grant-admin 'your-verified-email@example.com'
```

이 명령은 `ADMIN_EMAILS`에 계정을 추가합니다. 변경 후 API를 재시작합니다. 기본 허용 목록은 비어 있어 임의 관리자 계정을 만들지 않습니다.

실제 장치를 등록할 때는 ID와 이름을 지정합니다.

```powershell
.\.venv\Scripts\python.exe scripts\manage.py add-device 'dryer-01' '1번 건조기' --expected-seconds 2400
```

장치 ID·이름은 각각 최대 24자입니다. 장치 키는 `.local/device-keys.json`에 저장되고 서버에는 해시만 저장합니다. 센서 요청에는 `X-Device-Key` 헤더가 필요합니다. 재전송에는 같은 `event_id`와 같은 본문을 사용합니다. [장치 연동 계약](docs/device-integration.md)을 참고하세요.

## 검증

```powershell
.\.venv\Scripts\python.exe -m pytest -q
$env:TEST_USE_MYSQL = '1'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\db.py check
```

첫 테스트는 SQLite에서 동작하며, 두 번째는 별도 `jhy_test` DB에서 실제 MySQL 동작과 동시 요청을 검사합니다. 개발 DB에 테스트 데이터를 넣지 않습니다. 테스트에서는 SMTP와 FCM을 모의 처리합니다. 기존 `test/test_email.py`는 실제 Gmail 인증을 시도하는 수동 점검 파일이므로 자동 테스트 수집에서 제외했습니다.

## 외부 연결에 필요한 설정

- Gmail 주소·앱 비밀번호: 기존 `.env` 값을 개발 설정으로 복사했으며 실제 메일 발송은 수행하지 않았습니다.
- 휴대폰 푸시: `FCM_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` 및 앱에서 발급받은 FCM 토큰이 필요합니다. 서비스 계정 파일은 `.local/` 안에 두고 Git에 추가하지 마세요. 미설정 상태에서도 DB 알림 내역과 SSE는 동작합니다.
- 이용약관·개인정보 처리방침: 승인된 게시 URL을 `TERMS_URL`, `PRIVACY_URL`에 지정합니다. 임의의 법적 문구는 생성하지 않았습니다.
- 앱 화면, ESP32 펌웨어, 센서 보정·배선은 이 저장소에 없어 실물 연동을 검증하지 못했습니다.

기본 예상 건조 시간은 40분이며 통신 지연은 마지막 수신 후 120초를 기준으로 판단합니다. 예상 시간과 통신 지연 기준은 운영 설정이며 실측 결과로 보정해야 합니다. 완료·중단 판정은 Notion의 40분 기준을 사용하고, 정확히 40분인 경우 완료로 처리합니다.
