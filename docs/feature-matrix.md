# Notion 기능명세 대조표

기준: 현재 대화에서 제공한 Notion 프로젝트의 앱·관리자 33개, 임베디드 5개 항목을 직접 읽었습니다. 아래 경로 앞에는 `/api/v1`이 붙습니다. `구현 완료`는 서버 코드와 테스트 기준이며 앱 화면·실물 센서·실제 푸시 전달을 확인했다는 뜻은 아닙니다.

| ID / 기능 | Notion 요구사항 | 관련 API·모듈 | 최초 상태 | 현재 상태·남은 작업 |
|---|---|---|---|---|
| FNC-ADM-01 관리자 로그인 | [명세](https://app.notion.com/1f8324836d4f82c3bef881ab2679f05c) | POST /users/login, 관리자 허용 목록 | 미구현 | 공통 로그인 응답에 관리자 여부 표시, 관리자 API에서 권한 확인 |
| FNC-ADM-02 전체 건조기 상태 조회 | [명세](https://app.notion.com/570324836d4f825fa4bb81dea55cbac3) | GET /admin/devices | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-ADM-03 건조기 상세 정보 조회 | [명세](https://app.notion.com/141324836d4f826aa6dd0104b7502471) | GET /admin/devices/{id} | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-ADM-04 건조기 이용 불가 설정 및 해제 | [명세](https://app.notion.com/dbf324836d4f83ee9ee2813836e13817) | PATCH /admin/devices/{id}/availability | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-ADM-05 문의 및 오류 신고 목록 조회 | [명세](https://app.notion.com/52b324836d4f8282a50b010b1732945c) | GET /admin/inquiries: 상태·장치 필터 | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-ADM-06 문의 및 오류 신고 상세 조회 | [명세](https://app.notion.com/fcc324836d4f8277ae8f01f1a7d3078a) | GET /admin/inquiries/{id} | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-ADM-07 신고 처리 상태 번경 | [명세](https://app.notion.com/107324836d4f82aea1fc81887ef3e3af) | PATCH /admin/inquiries/{id}/status | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-ADM-08 공지사항 등록 및 관리 | [명세](https://app.notion.com/d7f324836d4f8308bf30817257ca5267) | GET/POST /admin/notices, PATCH/DELETE /admin/notices/{id} | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-ADM-09 건조기 사용 기록 조회 | [명세](https://app.notion.com/a1c324836d4f82b782c1019cc24731a3) | GET /admin/devices/{id}/history | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-01 건조기 목록 및 현재 상태 표시 | [명세](https://app.notion.com/fa5324836d4f83ed98e281d7bd71c4c2) | GET /devices, GET /state/all | 부분 구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-02 건조기 사용 가능 여부 표시 | [명세](https://app.notion.com/a1a324836d4f830db1d48120465cd38e) | GET /devices | 부분 구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-03 건조기 상세 상태 및 남은 시간 표시 | [명세](https://app.notion.com/c86324836d4f823f8d8d017e87ada539) | GET /devices/{device_id} | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-04 건조 진행 상태 시각화 | [명세](https://app.notion.com/deb324836d4f827d82b901c535052459) | GET /devices/{device_id}: progress, remaining_seconds | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-05 건조 완료 알림 | [명세](https://app.notion.com/d29324836d4f8273bfd781b6ff90baee) | 센서 이벤트 → notifications, FCM, SSE | 미구현 | 구현 완료: 이벤트·알림 생성·모의 전송 검증. FCM/휴대폰 실전송 검증 필요 |
| FNC-APP-06 건조기 일시정지·중단 알림 | [명세](https://app.notion.com/707324836d4f83d1aaed01fbc4288b3b) | paused/stopped 이벤트 → notifications | 미구현 | 구현 완료: 이벤트·알림 생성·모의 전송 검증. FCM/휴대폰 실전송 검증 필요 |
| FNC-APP-07 장시간 미수거 알림 | [명세](https://app.notion.com/c3c324836d4f83e18bff811105110856) | — | 미구현 | 보류 · 알림 생성, 조회, 발송, 설정 및 수거 확인 제거 |
| FNC-APP-08 알림 종류별 ON/OFF 설정 | [명세](https://app.notion.com/1d8324836d4f83d1851e0124dcd8690f) | GET/PATCH /users/me/settings | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-09 회원가입 및 로그인 | [명세](https://app.notion.com/0ab324836d4f82adad0901a0d84300ff) | POST /signup/email, /check/email_code, /users/signup, /users/login | 부분 구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-10 사용자 정보 및 설정 관리 | [명세](https://app.notion.com/fa8324836d4f8343b4d001fa8f2daee3) | GET/PATCH/DELETE /users/me, POST /logout | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-11 네트워크·서버·센서 오류 상태 표시 | [명세](https://app.notion.com/278324836d4f83e29aa081eb2ad10450) | GET /devices: 통신/센서 오류, DB 오류 503 | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-12 로딩 및 데이터 없음 상태 표시 | [명세](https://app.notion.com/0f8324836d4f83278530812413ded803) | 빈 배열, 404/503 응답 지원; 로딩 UI는 앱 구현 필요 | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-13 건조기 검색 / 필터 | [명세](https://app.notion.com/008324836d4f82b49c4301dcb45cddbb) | GET /devices?q=&state=&available= | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-14 건조기 즐겨찾기 | [명세](https://app.notion.com/c8b324836d4f83d9bc0c81c7b688d207) | — | 미구현 | 보류 · 즐겨찾기 API 및 목록 우선 표시 제거 |
| FNC-APP-15 알림 내역 | [명세](https://app.notion.com/7e4324836d4f83fa960f0113acce51c0) | GET /notifications, PATCH /notifications/{id}/read | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-16 건조기 사용 기록 | [명세](https://app.notion.com/645324836d4f827fa6eb81d2018314bd) | GET /users/me/history, /users/me/history/{cycle_id} | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-17 실시간 상태 갱신 | [명세](https://app.notion.com/66a324836d4f82978a4801d0350e2dda) | GET /devices, GET /info: 갱신 주기·수신 시각 | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-18 건조기 점검 / 이용 불가 표시 | [명세](https://app.notion.com/fe9324836d4f82018afd81ea3f382b89) | GET /devices: unavailable, unavailable_reason | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-19 공지사항 | [명세](https://app.notion.com/3d7324836d4f8389baf2816d2834f646) | GET /notices, /notices/{id} | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-20 문의 / 오류 신고 | [명세](https://app.notion.com/452324836d4f8278b193017f287cbad8) | POST/GET /inquiries | 미구현 | 문의 접수와 본인 신고 내역 조회 |
| FNC-APP-21 앱 설정 | [명세](https://app.notion.com/9fb324836d4f8263803901c1c0706f65) | GET/PATCH /users/me/settings, GET /info | 미구현 | 구현 완료: 설정 저장. 약관·개인정보 URL 지정 필요 |
| FNC-APP-22 이용 안내 | [명세](https://app.notion.com/037324836d4f8315925901ebfa79119e) | — | 미구현 | 보류 · 이용 안내 API 제거 |
| FNC-APP-23 비밀번호 찾기 | [명세](https://app.notion.com/72e324836d4f825b93c3013dec87c067) | POST /forget/password, /forget/check/email_code, /change/password | 부분 구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-APP-24 사용자 프로필 설정 | [명세](https://app.notion.com/0f2324836d4f82ed9a72017847540e98) | GET/PATCH /users/me, GET/PUT /users/me/image, 비밀번호 변경 | 미구현 | 구현 완료: 서버 API. 앱 화면 연동 검증 필요 |
| FNC-EMB-01 건조기 소비 전류 측정 | [명세](https://app.notion.com/096324836d4f83f4b2a6816e9f857216) | POST /devices/{id}/events | 서버 부분 구현 | 전류 수신·검증·저장과 센서 오류·복구 처리 검증 |
| FNC-EMB-02 건조기 진동 측정 | [명세](https://app.notion.com/d65324836d4f8251b38601a8774ae212) | POST /devices/{id}/events | 서버 부분 구현 | 가속도 배열 또는 진동수 수신·검증·저장 확인 |
| FNC-EMB-03 측정 결과 송신 | [명세](https://app.notion.com/a10324836d4f82439df981097b3d2cce) | PATCH /state/{id}, POST /devices/{id}/events | 서버 부분 구현 | 장치 인증, 중복 저장 방지와 충돌 응답을 실제 HTTP로 확인 |
| FNC-EMB-04 건조기 문 열림/닫힘 감지 | [명세](https://app.notion.com/887324836d4f827296ed813fb03bebb8) | — | 서버 부분 구현 | 보류 · 문 이벤트 API, 측정 필드 및 상태 처리 제거 |
| FNC-EMB-05 건조기 상태 판단 | [명세](https://app.notion.com/b9d324836d4f83d6b00e81218cdde8c2) | PATCH /state/{id}, POST /devices/{id}/events | 서버 부분 구현 | 전류·진동 감지값 검증과 사용 상태 판정, 완료·중단·알림 연계 확인 |

임베디드 항목은 서버가 담당하는 범위입니다. 완성 펌웨어의 실제 HTTP 형식과 실물 ESP32 접속은 별도 대조가 필요합니다.

백엔드 기능명세의 로그인·회원가입은 인증 테스트로, 중단/완료 검증은 실제 MySQL 경계값 테스트로 검증했습니다. 이름 없는 빈 기능 행은 구현 요구사항으로 추정하지 않았습니다. 구독 정책은 사용자가 승인한 ‘한 장치에 여러 사용자 구독’을 적용합니다. 현재 경로는 [API 참조](api.md)에서 확인할 수 있습니다.

