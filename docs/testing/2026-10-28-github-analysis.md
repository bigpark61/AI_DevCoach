# GitHub 분석 v2 검증 기록

- 요청자/협업 계정: 최석준 / `hahahoho12360`
- 실행 주체: 최석준의 요청에 따라 Codex가 수행한 자동 검사
- 검사일: 2026-10-28 (한국 시간)
- 입력: 팀에서 전달한 `AI_DevCoach_v2.zip`
- 입력 ZIP SHA-256: `4e757cb30880b2d8e2edcb9b3ece1bfb1c94d3cceb10ed3174c19db3358acc68`
- 비교 기준: `main`의 `947ddb0f1a61ac9ab8413b779e676656179e73d3`
- 작업 브랜치: `feature/github-analysis`

## 작업 범위와 출처

첨부 v2에 이미 들어 있던 GitHub 분석 구현을 기존 저장소와 비교하여 업로드할 변경분을 준비했다. 이 문서는 최석준이 해당 기능을 처음부터 직접 작성했거나 Windows에서 수동 테스트를 마쳤다는 뜻이 아니다. 현재 완료한 작업은 제공 소스 확인, 변경분 준비, 자동 실행 검증, 결과 문서화다.

GitHub 연동 앱으로 브랜치를 만들려 했으나 `403: Resource not accessible by integration`으로 거부되었다. 연결 계정의 저장소 메타데이터에는 push 권한이 표시되지만, 이번 실행에서 원격 브랜치·커밋·PR은 생성하지 못했다. 사용자가 직접 업로드하고 PR을 만든 후 해당 링크를 추가해야 한다.

다음 5개 파일이 기능 변경분이다. 텍스트 줄바꿈은 LF로 통일했다.

| 파일 | 변경 내용 |
| --- | --- |
| `backend/main.py` | 공개 GitHub 저장소 분석 및 사용자별 이력 API |
| `frontend/app.js` | GitHub 분석 메뉴, 입력 화면, 결과 및 이력 |
| `frontend/styles.css` | 분석 화면 스타일 |
| `migrations/versions/0002_github_analysis.py` | 분석 이력 테이블 마이그레이션 |
| `tests/test_app.py` | GitHub 분석 및 잘못된 URL 관련 테스트 |

기존 `README.md` 안내와 `.github/workflows/tests.yml`은 보존했다. README에는 이번 검증 기록과 협업 안내 링크만 추가했다. `.env`, `.neon`, 원본 `data/`, `.venv/`, `node_modules/`, 캐시, 새 실행 로그는 업로드하지 않았다. 기존 저장소에 이미 있던 로그 등은 이번 변경에서 삭제하지 않았다.

## 검사 환경

- Linux, Python 3.12.14, Node.js 24.22.1.
- 프로젝트 `requirements.txt`를 별도의 검사 가상환경에 설치.
- 주요 설치 버전: FastAPI 0.162.0, Starlette 1.10.0, httpx 0.28.1, OpenAI 2.54.0, Pydantic 2.14.1, psycopg 3.3.6, SQLAlchemy 2.1.6, Alembic 1.20.1.
- 원본 `.env`와 원본 SQLite 데이터베이스를 사용하지 않음.
- 자동 테스트는 테스트별 임시 SQLite 데이터베이스를 사용.

이 실행 환경에는 SOCKS 프록시가 설정되어 있어 첫 실행에서 `socksio` 누락으로 1건이 실패했다. 검사 환경에만 `socksio==1.0.0`을 설치한 후 10건 모두 통과했다. 이 환경 전용 패키지를 프로젝트 요구사항에 추가하지 않았다.

## 검사 결과

| 검사 | 결과 | 확인 범위 |
| --- | --- | --- |
| `python -m unittest discover -s tests -v` | 10건 통과, 2.151초 | 첨부된 전체 자동 테스트 |
| `python -m compileall -q backend migrations` | 통과 | Python 구문 검사 |
| `node --check frontend/app.js` | 통과 | JavaScript 구문 검사 |
| Uvicorn 실행 후 `GET /` | HTTP 200 | 시작 HTML 제공 |
| `GET /static/app.js` | HTTP 200 | JavaScript 파일 제공 |
| `GET /static/styles.css` | HTTP 200 | CSS 파일 제공 |
| `GET /api/health` | HTTP 200 | `{"status":"ok","database":"sqlite"}` |
| 업로드 파일 점검 | 지정 5개 소스에서 검사한 키·토큰·DB URL 패턴 일치 없음 | 모든 종류의 비밀정보 부재를 보증하는 전수 보안감사는 아님 |

자동 테스트 10건:

1. 회원가입 동의 여부와 이메일 중복 검사
2. 로그인·로그아웃 및 세션 쿠키
3. 프로필 입력 검증과 인증
4. 공개 GitHub 분석, 비밀값 마스킹, 사용자별 분석 이력 분리
5. GitHub 저장소가 아닌 URL의 사전 거부
6. 진단 저장·재개·채점·학습 계획 및 진도 흐름
7. 학습 시간 한도와 다른 사용자 계획 접근 제한
8. 문제은행 구조
9. OpenAI 구조화 채점 요청 및 응답 처리
10. OpenAI 키 누락 시 답안 보존과 재시도

테스트 출력 마지막 부분:

```text
Ran 10 tests in 2.151s

OK
```

## 아직 확인하지 않은 범위

- 테스트에서 GitHub API는 모의 응답을 사용했다. 실제 공개 GitHub API 연결은 별도로 확인해야 한다.
- OpenAI 채점은 모의 HTTP 응답으로 검사했다. 실제 유료 API 호출과 GitHub 분석의 OpenAI 응답 경로는 검증하지 않았다.
- 운영 Neon/PostgreSQL 연결과 실제 데이터베이스 마이그레이션을 실행하지 않았다. PostgreSQL 배포 시 담당자가 `python -m alembic upgrade head`를 적용해야 한다.
- 브라우저 실행 파일이 없어 화면 렌더링 및 클릭 테스트는 수행하지 못했다. HTTP 200과 JavaScript 구문 검사만으로 화면의 모든 동작이 정상이라고 판단하지 않는다.
- 최석준의 Windows PC 실행 및 팀원의 독립 리뷰는 남아 있다.
- Starlette가 httpx TestClient에 대한 사용 중단 예정 경고를 출력했으나 테스트는 통과했다.

## 재현 방법

실제 키나 운영 DB 설정이 없는 새 체크아웃에서 실행한다. 기본 SQLite 모드는 `.env`가 없어도 실행된다. 실제 값을 넣지 않은 `.env.example`을 그대로 `.env`로 복사하면 예시 PostgreSQL 주소를 사용하게 되므로, 기본 실행 시 복사하지 않는다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q backend migrations
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`과 `http://127.0.0.1:8000/api/health`를 확인한다. 테스트 환경 자체가 SOCKS 프록시를 사용할 때만 `python -m pip install "httpx[socks]"`가 추가로 필요할 수 있다.
