# 2026년 11월 18일 채팅 이력 캐시 헤더 수정 및 검증

최석준 담당 Lint 도입 과제의 후속 검증에서 남은 실패를 해결한 기록이다.
사용자가 제공한 Windows CMD 화면에는 Ruff·Black·ESLint·컴파일 통과와
기능 테스트 30개 중 캐시 헤더 테스트 1개 실패가 표시되어 있었다.
아래 수정 후 결과는 Codex의 보조 검증 환경에서 실행한 실제 결과다.
사용자 PC의 수정 후 재검증과 원격 커밋·푸시·PR은 별도로 확인해야 한다.

## 원인과 수정

GET /api/agent/history는 로그인한 사용자의 채팅 이력을 반환하지만,
응답에 Cache-Control: no-store와 Vary: Cookie가 설정되어 있지 않았다.
기존 test_authenticated_history_cannot_be_cached는 두 헤더를 기대했으며,
첫 번째 검사에서 None != 'no-store'로 실패했다.

backend/main.py의 agent_chat_history에 다음 세 줄을 추가했다.

```python
response: Response,
```

```python
response.headers["Cache-Control"] = "no-store"
response.headers["Vary"] = "Cookie"
```

첫 줄은 함수의 첫 번째 매개변수이고, 다음 두 줄은 함수 본문의 첫 부분이다.
Response는 이미 fastapi에서 가져오고 있으므로 import 추가가 필요하지 않다.
no-store는 브라우저와 공유 캐시에 응답을 저장하지 말라는 지시이고,
Vary: Cookie는 응답이 요청의 Cookie 값에 따라 달라진다는 표시다.
Vary는 인증 검증을 대신하지 않는다. DB의 채팅 기록을 삭제하는 변경도 아니다.
수정 범위는 이 API의 정상 응답 헤더이며 모든 API나 기존 캐시 전체를 정리한 것은 아니다.

테스트 기대값·Lint 규칙·검사 대상을 완화하지 않았다. DB 스키마, 쿼리,
반환 JSON 구조, 인증 조건은 변경하지 않았다. 기존 테스트가 회귀 검증을 제공한다.

## 실제 검증 결과

| 검사 | 수정 전 | 수정 후 |
| --- | --- | --- |
| Ruff | PASS | PASS |
| Black | PASS | PASS, Python 14개 파일 형식 유지 |
| ESLint | PASS | PASS |
| unittest | 30개 중 29개 성공, 1개 실패 | 30개 모두 성공, OK |
| 컴파일 | PASS | PASS |
| 공통 스크립트 종료 코드 | 1 | 0 |

실행 명령은 scripts/check_quality.py --test다. 보조 환경에만 존재하는
SOCKS 프록시 변수는 외부 요청이 모의 처리되는 테스트 프로세스에서만 제외했다.

```bash
env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u http_proxy \
  -u HTTPS_PROXY -u https_proxy \
  .venv/bin/python scripts/check_quality.py --test
```

실제 출력 요약은 다음과 같다. 실행 시간은 매번 달라질 수 있다.

```text
Ran 30 tests in 5.415s
OK
PASS | Python lint (Ruff) | exit=0
PASS | Python format (Black) | exit=0
PASS | JavaScript/TypeScript lint (ESLint) | exit=0
PASS | Application tests | exit=0
PASS | Python compilation | exit=0
```

Starlette TestClient의 httpx 사용 중단 예정 경고는 남아 있다. 테스트 중 출력된
Invalid RAG-assisted plan; using rules-based plan 메시지는 AI 계획의 출처 근거가
잘못되었을 때 기본 계획으로 전환하는 테스트 경로에서 발생하며 실패 자체가 아니다.
경고와 fallback 메시지를 숨기지 않았다.

## Windows에서 재현

기존 Lint 패치를 적용한 작업 폴더에서 후속 패치를 적용하고 다음을 실행한다.

```cmd
.venv\Scripts\python.exe scripts/check_quality.py --test
echo %ERRORLEVEL%
```

30개 테스트 OK, 다섯 항목 PASS, 종료 코드 0을 확인한다.
실제 결과와 커밋·PR 주소는 [담당 기여 기록](../seokjun-lint-contribution.md)에 적는다.

## 검증 범위와 근거

운영 PostgreSQL, 실제 AI 호출, 실제 브라우저 및 Vercel 운영 배포는 검증하지 않았다.
로컬 테스트 통과를 운영 정상 동작의 증거로 확대하지 않는다.
이 후속 작업에서는 원격 쓰기를 재시도하지 않았다. 이전 연결의 권한 오류가
해결되었다는 근거가 없으므로 사용자가 본인 계정으로 커밋·푸시하도록 안내한다.

- 멘토링 일지 2026년 11월 16일 1.2·1.3·2.1 및 AI 개발 지침
- [FastAPI Response Headers](https://fastapi.tiangolo.com/advanced/response-headers/)
- [RFC 9111 HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)
- tests/test_chat_persistence.py의 test_authenticated_history_cannot_be_cached
