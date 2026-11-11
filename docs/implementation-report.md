# 작업 결과 보고서

이 문서는 초기 구현 당시의 기록입니다. 이후 보류된 네 기능과 관련 API를 제거했습니다. 현재 기능 범위와 경로는 [기능 대조표](feature-matrix.md)와 [API 참조](api.md)를 기준으로 확인합니다.

기준일: 2026-11-07, Asia/Seoul. 현재 대화에서 제공한 저장소·Notion·ERD를 기준으로 작업했습니다. 서버 구현과 실제 로컬 MySQL 연동을 완료했으며, 외부 계정과 실물 환경이 필요한 검증은 아래에서 별도로 구분합니다.

## 1. 프로젝트 분석 요약

기존 구조는 `main.py`, `api/v1/endpoints`, `Schemas`, `auth`, `models`, `database`이며 동기 SQLAlchemy 세션을 사용하는 FastAPI 프로젝트였습니다. 완성된 것으로 표시된 기능 중에서도 실제 실행을 막는 결함을 확인했습니다.

- 세션 생성의 `Session_id` 생성자 인자 오류, naive/aware datetime 비교 오류를 격리된 DB 실행으로 재현했습니다.
- 개별 상태 조회의 잘못된 select 구문과 구독 조건식의 Python 비트 연산 오류를 재현했습니다.
- 회원/구독 로그의 UUID 기본값 누락, 전체 상태 조회 오류, 구독 라우터 미등록, 취소 조건 반전은 코드와 후속 회귀 테스트로 확인했습니다.
- 기존 가상환경이 참조하던 Python 3.13이 없었습니다. 3.13.17을 설치하고 기존 `venv`와 별도로 `.venv`를 구성했습니다. 기존 Python 3.15 환경은 변경하지 않았습니다.
- 기존 로컬 DB 설정 주소에는 MySQL 리스너가 없었으며, 이번 작업의 DB는 별도 포트·데이터 디렉터리로 구축했습니다.

기존 API 경로·성공 응답·Argon2·동기 DB 의존성 구조를 유지했습니다. `database/base.py`, `models/devices.py`, `Dockerfile`, 기존 수동 SMTP 점검 파일은 수정하지 않았습니다. 미완성 흐름과 신규 기능 연결에 필요한 파일을 수정했으며, 기존 기능이 전혀 변경되지 않았다고 일괄 주장하지 않습니다. 인증코드 DB 저장, 입력 검증, 장치 인증, 복구 세션 제한 등은 이번 보완 사항입니다.

## 2. 기능별 구현 현황

[기능 대조표](feature-matrix.md)는 기능명세의 앱·관리자 33개와 임베디드 5개를 각각 추적합니다. [원문 추출](requirements-source.json), [기존 API 계약](notion-api-contract.json), [현재 API 참조](api.md)를 함께 제공합니다.

| 구분 | 결과 |
|---|---|
| 기존 인증·세션·상태 조회 | 결함을 수정하고 실제 MySQL에서 회귀 검증 |
| 구독 | 사용자·장치 복합 키, 동시 사용자 구독, 본인 구독만 취소, 종료 시 자동 해제 |
| 상태·사용 기록 | 센서 원본 저장, 중복·과거 이벤트 처리, 완료/중단 경계, 사용 기록·검색·진행률·통신 지연 |
| 사용자 기능 | 프로필·이미지·설정·즐겨찾기·회원탈퇴·공지·문의·알림 내역·읽음·SSE |
| 관리자 기능 | 관리자 로그인, 상태·이력 조회, 이용 불가 설정, 문의 처리, 공지 CRUD·상단 고정 |
| 알림 서버 | 완료·일시정지·중단·미수거 생성, FCM 어댑터·재시도·세션별 토큰·기기별 중복 재시도 방지 |
| 검증 필요 | 실제 Gmail 인증/발송, FCM 휴대폰 도달, 앱 화면, ESP32 측정·보정·송신·문 센서 |

기존 Notion API 작업 15개는 모두 유지했고 필요한 API를 추가했습니다. 현재 OpenAPI에는 유효한 HTTP 경로 50개, 작업 60개가 있습니다. 기존의 빈 경로 등록은 코드에 남기고 문서에서 제외했으며 루트 `/` 경로를 정상 제공했습니다.

문서 충돌과 미정 사항은 다음과 같이 처리했습니다.

- 사용자 답변에 따라 한 건조기에 여러 사용자가 구독하도록 구현했습니다. 이전 문서의 독점 선택 조건은 적용하지 않았습니다.
- 필요한 신규 테이블 추가는 사용자 승인을 반영했습니다. 관리자 권한은 기존 검증 계정에 대한 환경변수 허용 목록을 사용하며 기본값은 권한 없음입니다.
- 중단/완료는 40분 기준이고, 명세에서 경계가 비어 있던 정확히 40분은 완료로 처리했습니다.
- 예상 시간 40분, 미수거 10분, 통신 지연 120초, 측정 시각 미래 허용 5분은 명시적으로 기록한 개발 기본값입니다. 원시 센서 단위·임계치와 실제 건조 시간은 실측 보정 대상입니다.
- 신규/변경 비밀번호 8~128자, 이미지 크기 제한 등 명세에 수치가 없는 입력 제한은 개발 기본 정책입니다.
- 앱·펌웨어 소스가 이 백엔드 저장소에 없어 UI와 하드웨어 측정 코드를 구현하거나 실물 동작을 검증한 것으로 표시하지 않았습니다. 해당 기능에 필요한 서버 API와 계약은 제공합니다.

## 3. 실제 코드 변경 사항


### 새로 생성한 파일

| 파일 | 목적 |
|---|---|
| `.env.example` | 환경변수·설정 예시; 기존 .env 보존 |
| `README.md` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `Schemas/application.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `Schemas/fields.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `alembic.ini` | 명시적 초기/추가 마이그레이션; 파괴적 다운그레이드 비활성화 |
| `api/v1/endpoints/account.py` | 프로필·이미지·설정·계정 삭제 API |
| `api/v1/endpoints/devices.py` | 상태·검색·즐겨찾기·사용 기록·점검 관리 API |
| `api/v1/endpoints/info.py` | 앱 설정 메타데이터·이용 안내 API |
| `api/v1/endpoints/inquiries.py` | 사용자 문의와 관리자 조회·상태 변경 API |
| `api/v1/endpoints/notices.py` | 공지 목록·상세·상단 고정·관리자 CRUD |
| `api/v1/endpoints/notifications.py` | 알림 내역·읽음·SSE·푸시 토큰 API |
| `auth/auth_admin.py` | 기존 사용자 세션을 활용한 관리자 이메일 허용 목록 검사 |
| `config.py` | 환경변수·설정 예시; 기존 .env 보존 |
| `database/schema.sql` | Alembic과 동일한 실행용 MySQL 스키마 SQL |
| `database/types.py` | MySQL의 UTC DATETIME(6) 정밀도 유지 |
| `docs/api.md` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/database-schema.json` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/database.md` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/device-integration.md` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/erdcloud-original.sql` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/feature-matrix.md` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/implementation-report.md` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/notion-api-contract.json` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/openapi.json` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/requirements-source.json` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `docs/verification.json` | 요구사항 근거·API/DB 계약·운영 방법·검증 결과 문서화 |
| `migrations/env.py` | 명시적 초기/추가 마이그레이션; 파괴적 다운그레이드 비활성화 |
| `migrations/script.py.mako` | 명시적 초기/추가 마이그레이션; 파괴적 다운그레이드 비활성화 |
| `migrations/versions/0001_initial_schema_with_documented_.py` | 명시적 초기/추가 마이그레이션; 파괴적 다운그레이드 비활성화 |
| `migrations/versions/0002_scope_push_tokens_and_persist_per_.py` | 명시적 초기/추가 마이그레이션; 파괴적 다운그레이드 비활성화 |
| `models/__init__.py` | 전체 모델을 마이그레이션에 명시적으로 등록 |
| `models/account.py` | 프로필·사용자 설정·인증코드·로그인 실패 기록 테이블 |
| `models/inquiry.py` | 문의/오류 신고 테이블 |
| `models/notice.py` | 공지 테이블 |
| `models/notification.py` | 알림·세션별 푸시 토큰·토큰별 전달 기록 |
| `models/operations.py` | 장치 실행 상태·인증키 해시·건조 주기·참여자·원본 이벤트 테이블 |
| `pytest.ini` | 격리된 API·권한·상태 전이·FK·동시성 회귀 검증; 실발송 모의 처리 |
| `requirements-dev.txt` | 테스트·정적 검사 도구 버전 고정 |
| `scripts/db.py` | DDL 권한을 앱과 분리한 마이그레이션·스키마 검사·SQL 생성 |
| `scripts/local_mysql.py` | 프로젝트 전용 서버 설치·기동·상태·종료; 기존 데이터 초기화 거부 |
| `scripts/manage.py` | 검증 계정 관리자 지정·장치 등록과 키 발급 |
| `scripts/run.ps1` | 재현 가능한 로컬 서버 실행·상태 확인 |
| `services/common.py` | UTC·UUID 직렬화 공통 함수 |
| `services/devices.py` | 센서 이벤트 검증·행 잠금·건조 판정·구독 정리·상태 뷰 |
| `services/notifications.py` | 미수거 스케줄·영속 알림·FCM 재시도·토큰별 전달 |
| `tests/conftest.py` | 격리된 API·권한·상태 전이·FK·동시성 회귀 검증; 실발송 모의 처리 |
| `tests/test_application.py` | 격리된 API·권한·상태 전이·FK·동시성 회귀 검증; 실발송 모의 처리 |
| `tests/test_auth.py` | 격리된 API·권한·상태 전이·FK·동시성 회귀 검증; 실발송 모의 처리 |
| `tests/test_concurrency.py` | 격리된 API·권한·상태 전이·FK·동시성 회귀 검증; 실발송 모의 처리 |
| `tests/test_devices.py` | 격리된 API·권한·상태 전이·FK·동시성 회귀 검증; 실발송 모의 처리 |

### 수정한 파일

| 파일 | 목적 |
|---|---|
| `.dockerignore` | 개발 런타임·비밀 설정·DB 데이터가 Git/이미지에 포함되지 않도록 제외 |
| `.gitignore` | 개발 런타임·비밀 설정·DB 데이터가 Git/이미지에 포함되지 않도록 제외 |
| `Schemas/auth_email_schema.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `Schemas/auth_password.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `Schemas/email_code_schema.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `Schemas/forget_password.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `Schemas/login_schema.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `Schemas/senser_schema.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `Schemas/signup_schema.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `Schemas/subscribe_schema.py` | 기존 필드 호환 유지 및 입력 범위·코드·비밀번호·센서 검증 |
| `api/v1/endpoints/email_contify.py` | DB 기반 인증코드 연동·중복 이메일 오류 상태 수정 |
| `api/v1/endpoints/load_state.py` | 전체/개별 조회 쿼리 오류 수정 |
| `api/v1/endpoints/login.py` | 비밀번호 인증·세션·관리자 로그인·10회 실패 잠금 |
| `api/v1/endpoints/logout.py` | 실제 세션 삭제·쿠키 제거·세션별 푸시 토큰 해제 |
| `api/v1/endpoints/password.py` | 본인 인증·코드 목적 검증·비밀번호 변경·세션 무효화 |
| `api/v1/endpoints/signup.py` | UUID 생성·인증코드 소비·중복 오류 처리 |
| `api/v1/endpoints/subscribe.py` | 다중 사용자 구독·취소·명세 경로 연결 |
| `api/v1/endpoints/update_state.py` | 장치 인증·필드 호환·이벤트 수신·문 이벤트 연결 |
| `auth/auth_email.py` | SMTP 흐름 유지, 인증코드 DB 저장·목적 분리·만료·재시도 제한 |
| `auth/auth_session.py` | 세션 키·쿠키·UTC 만료 오류 수정, 비밀번호 복구 세션 권한 분리 |
| `database/connection.py` | 기존 동기 DB 구조 유지, 환경 파일 선택·연결 확인·실패 시 롤백 |
| `main.py` | 미등록·신규 라우터 연결, 작업 수명 관리, DB 오류 응답, 헬스체크 |
| `models/favorite.py` | 복수 장치 즐겨찾기를 막던 user_id 단독 UNIQUE 제거 |
| `models/session_model.py` | UTC 시간 정밀도·복구 목적·비밀번호 검증 시각 |
| `models/state.py` | UTC 이벤트 시각 정밀도 |
| `models/state_log.py` | 조회 인덱스·UTC 정밀도·SQLite 테스트 호환 |
| `models/subscribe.py` | 사용자·장치 복합 PK 및 조회 인덱스 |
| `models/subscribe_log.py` | 로그 UUID 기본값 보완 |
| `models/users.py` | 누락된 UUID 기본값 보완 |
| `requirements.txt` | 기존 버전 유지, 필요한 추가 의존성 고정, UTF-8 텍스트로 정규화 |

## 4. MySQL 데이터베이스 구축 결과

- Oracle 공식 ZIP의 체크섬을 확인해 MySQL 8.4.13을 프로젝트 `.local/`에 설치했습니다. Workbench 26.10.0도 설치·실행했습니다.
- 개발 서버는 `127.0.0.1:3307`, 개발 DB는 `jhy_development`, 격리 테스트 DB는 `jhy_test`입니다. 기존 `.env`를 보존하고 `.env.local`을 사용합니다.
- ORM 테이블 22개와 Alembic 버전 테이블을 포함해 총 23개가 존재합니다. 기존 ERD의 8개 테이블과 기능에 필요한 추가 14개입니다. FK 27개 및 복합 PK·UNIQUE·조회 인덱스를 검사했습니다.
- `0001`, `0002` 마이그레이션을 실제 적용했고, `alembic check`에서 추가 변경 사항이 없음을 확인했습니다. 초기화를 다시 요청해도 기존 데이터 디렉터리를 재생성하지 않고 실행 중인 서버를 재사용합니다.
- `JHY Local Development` Workbench GUI에서 실제 연결 상태와 23개 테이블 목록을 확인했습니다. 비밀번호는 Windows 자격 증명 저장소에 저장했으며 연결 설정에 평문을 넣지 않았습니다.
- FastAPI를 실행하고 실제 HTTP 접근을 확인했습니다. 일반 앱 계정은 CRUD 권한만 사용하며 스키마 변경은 별도 관리 자격 증명을 사용합니다.

[전체 컬럼·PK/FK·UNIQUE·인덱스](database.md), [기계 판독용 스키마](database-schema.json), [실행용 SQL](../database/schema.sql), [원본 ERD 내보내기](erdcloud-original.sql)를 제공합니다.

ERD 차이는 다음과 같습니다.

| 원본 ERD / 코드 차이 | 반영 결과 |
|---|---|
| ERD Subscribe 복합 PK, 기존 모델은 장치만 PK | 사용자 승인 정책과 ERD에 맞춰 복합 PK로 수정 |
| Favorite 모델의 user_id 단독 UNIQUE | ERD와 복수 즐겨찾기에 맞춰 제거 |
| ERD session 컬럼, 기존 코드 session_id 컬럼 | 기존 코드 연동을 보존해 session_id 사용; 차이 기록 |
| ERD의 한글 현재시각 기본값, State_log의 not_subscribed 기본값 | 유효한 CURRENT_TIMESTAMP와 상태 의미에 맞는 not_used 사용 |
| ERD의 일부 UNIQUE 의미가 주석으로만 존재 | 기존 ORM의 명시적 email·장치 이름 등 제약 보존 |
| 공지·문의·알림·주기·환경 설정 테이블 부재 | 사용자 승인에 따라 추가; 실제 스키마 문서에 모두 기록 |
| MySQL 시간 정밀도·UUID 생성 누락 | DATETIME(6) UTC 일관성과 애플리케이션 UUID 기본값 보완 |

원본 ERD SQL은 설계 근거이며 그대로 실행하지 않습니다. 실제 생성에는 마이그레이션 또는 실행용 SQL을 사용합니다. 기존 운영 DB의 데이터 삭제·초기화는 수행하지 않았습니다.

## 5. 테스트 결과

| 검사 | 결과 |
|---|---|
| 실제 MySQL API·회귀 테스트 | 49개 통과, 실패 0 |
| SQLite API·회귀 테스트 | 48개 통과, MySQL 전용 동시성 1개 생략 |
| 기존 Notion API 계약 | 15개 메서드·경로 보존; 별도 최종 계약 검사 통과 |
| 실제 HTTP 실행 점검 | 10개 URL의 정상/인증 거부 응답 확인 |
| SQLAlchemy / Alembic | 전체 모델 로딩·마이그레이션·스키마 일치 확인 |
| 동시 요청 | 두 사용자 동시 구독, 동일 센서 이벤트 재전송, 동일 이메일 코드 발송 경쟁 검증 |
| 보안·오류 처리 | 401/403/409/422/429/503, 코드 재사용·목적 혼동 방지, 복구 세션 제한, 본인 데이터 접근, 세션 무효화 |
| 상태·알림 | 2399/2400/3000초 경계, 하트비트·재개 시 시작 시각 유지, 구독 정리, 미수거 취소, 푸시 재시도·중복 방지, SSE |
| 데이터 무결성 | 실제 MySQL의 FK, 복합 PK, 여러 장치 즐겨찾기, 계정 삭제 참조 정리 |
| 정적 검사 | 변경 Python 파일 Ruff E9/F, 컴파일, 의존성 검사, Git diff 공백 검사 통과 |
| Gmail 수동 점검 | SMTPServerDisconnected로 연결이 끊겨 실계정 인증 검증 미완료. 실제 이메일 발송 없음 |
| 실제 FCM·휴대폰 | 자격 증명/앱 토큰이 없어 미실행. 모의 전달·재시도 검증 완료 |

테스트 중 MySQL 기본 REPEATABLE READ에서 잠금을 기다린 요청이 이전 스냅샷을 읽는 문제를 발견해 변경용 조회를 보강했고 동시성 테스트가 통과했습니다. 푸시 수신 토큰이 없는 과거 알림으로 큐가 막히는 문제와 여러 기기 중 성공한 기기에 재전송하는 문제도 수정·검증했습니다.

기존 자동 회귀 테스트는 없었고 `test/test_email.py`는 SMTP 로그인 점검용 파일이었습니다. 이를 실제로 별도 실행해 위 연결 문제를 확인했습니다. SMTP/FCM 기능 테스트에서는 모의 전송을 사용했습니다. 외부 라이브러리의 테스트 API 폐기 예정 경고 2개는 남아 있지만 실패는 없습니다. Docker와 실물 앱·센서는 제공된 실행 환경에 없어 검증하지 않았습니다.

구조화된 최종 검사 결과는 [verification.json](verification.json)에 있습니다. `.local/test-results-mysql.xml`, `.local/test-results-sqlite.xml`에는 로컬 테스트 결과가 있습니다.

## 6. 남은 작업과 필요한 정보

1. **Gmail 연결 확인:** 후속 점검에서 SMTP 인증과 실제 가입 흐름을 확인했습니다.
2. **실제 관리자 계정:** 후속 점검에서 사용자 지정 계정의 가입을 확인하고 관리자 권한을 반영했습니다.
3. **휴대폰 푸시:** Firebase 프로젝트·서비스 계정과 모바일 앱 FCM 토큰이 필요합니다. 앱에서 토큰 등록·해제, 알림 클릭 이동, notification_id 중복 제거를 연결해야 합니다.
4. **실물 ESP32·센서:** 장치 등록, 키 설정, 측정 단위·전류/진동 임계치·실제 건조 시간 보정, 재전송 큐·Wi-Fi·문 센서 시험이 필요합니다. 백엔드 수신 계약과 수거 확인 대체 API는 제공했습니다.
5. **프론트엔드:** 앱 화면·로딩·아이콘·테마 적용과 API 호출을 앱 소스에 연결해야 합니다. 이 저장소의 API 구현만으로 앱 화면이 완성된 것은 아닙니다.
6. **운영 문서:** 승인된 이용약관·개인정보 처리방침 URL을 설정해야 합니다. 운영 배포·공개 네트워크·TLS 설정과 Docker 실행은 이번 로컬 검증에 포함되지 않습니다.

서버 실행·계정 지정·장치 등록의 정확한 명령은 [README](../README.md)에 있습니다. 현재 로컬 API와 MySQL은 실행 중이며 비밀 설정과 DB 데이터는 Git에서 제외되어 있습니다.

## 후속 점검

FastAPI와 MySQL을 다시 시작하고 상태 조회 응답을 확인했습니다. 현재 백엔드의 인증 테스트 16개가 MySQL에서 통과했습니다.

Gmail 앱 비밀번호를 갱신한 뒤 `.env.local` 설정으로 SMTP 인증에 성공했습니다. API를 재시작한 후 실제 인증번호 발송, 코드 확인, 회원가입 요청이 각각 HTTP 200을 반환했고 로컬 MySQL에 가입 계정이 저장됐습니다.

가입한 계정을 관리자 허용 목록에 추가하고 API를 재시작했습니다. 공통 로그인과 관리자 장치 목록 조회가 각각 HTTP 200을 반환했고 로컬 MySQL에서 해당 계정의 유효한 로그인 세션을 확인했습니다. 세션 없는 요청에는 관리자 API가 HTTP 401을 반환했습니다.

별도 MySQL 테스트 DB에서 공지 등록·수정·삭제와 상단 고정, 문의 조회와 처리 상태 변경, 건조기 이용 가능 상태 변경을 검증했습니다.

사용자 요청에 따라 후속 작업 범위는 백엔드의 이메일 인증과 관리자 계정 설정으로 좁혔습니다.

## ESP32 통신 백엔드 후속 작업

Notion의 기존 장치 상태 업데이트 API 형식을 유지했습니다. 이벤트 API는 전류 숫자, 가속도 배열 또는 진동수, 측정 실패와 복구를 처리합니다. 펌웨어가 보정한 전류·진동 감지 여부로 서버가 사용 상태를 판정할 수 있습니다.

문과 전류·진동의 최신 측정 시각을 분리했습니다. 문 열림·닫힘이 종료 측정보다 먼저 도착하거나 문 열림이 뒤늦게 도착해도 사용 기록과 수거 상태를 반영합니다. 기존 데이터가 들어 있는 임시 MySQL에서 `0002 → 0003` 마이그레이션과 기존 요청 재전송을 검증한 뒤 개발 DB에 적용했습니다.

별도 MySQL DB와 실제 로컬 HTTP 서버로 장치 인증, 기존 응답, 이벤트 재전송, 충돌 응답, 종료와 수거, 오류와 복구를 확인했습니다. MySQL 회귀 테스트 52개와 SQLite 51개가 통과했습니다. SQLite에서 건너뛴 행 잠금 테스트는 MySQL에서 실행했습니다.

팀 저장소에는 전류 측정 예제만 있고 별도의 HTTP 예제는 온도 샘플을 전송했습니다. 완성 펌웨어의 요청 경로·본문·인증 방식과 실제 장치 접속은 확인이 남았습니다. 기본 개발 서버는 로컬 주소에서 실행 중이며 LAN에서 받을 주소를 지정하는 실행 옵션을 제공했습니다.
