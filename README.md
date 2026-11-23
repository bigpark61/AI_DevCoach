# AI DevCoach

> **AI 기반 자기주도 학습 및 프로젝트 코칭 플랫폼**  
> AI-native Final Project · 최종 제출용 README  · 2026-11-19 정리

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [팀원 및 역할](#2-팀원-및-역할)
3. [주요 기능 및 구현 범위](#3-주요-기능-및-구현-범위)
4. [기술 스택](#4-기술-스택)
5. [시스템 아키텍처](#5-시스템-아키텍처)
6. [핵심 AI 기술](#6-핵심-ai-기술)
7. [설치 및 실행](#7-설치-및-실행)
8. [테스트 및 검증 결과](#8-테스트-및-검증-결과)
9. [실사용자 테스트 및 피드백](#9-실사용자-테스트-및-피드백)
10. [배포 및 관련 링크](#10-배포-및-관련-링크)
11. [보안·개인정보 및 AI 사용 고지](#11-보안개인정보-및-ai-사용-고지)
12. [제출 전 점검표 

## 1. 프로젝트 소개

### 1.1 개요

AI DevCoach는 개발 학습자가 **역량 진단 → 개인화 학습계획 → 학습·과제 수행 → AI 질의응답 및 피드백 → 학습 현황 확인** 과정을 경험할 수 있도록 지원하는 웹 기반 학습 코칭 서비스입니다. 학습자 수준과 학습자료를 결합하여 일률적인 강의 안내가 아닌 맥락 기반 코칭을 제공하는 것이 목표입니다.

### 1.2 해결하려는 문제

- 학습자가 자신의 개발 역량과 부족한 영역을 객관적으로 파악하기 어려움
- 학습 목표와 가용 시간에 맞는 실행 가능한 계획 수립이 어려움
- 개발 도중 오류·개념 질문에 대해 즉각적인 도움을 얻기 어려움
- 학습·과제 진행 상황을 지속적으로 관리하기 어려움

### 1.3 대상 사용자 및 목표

- **대상:** Python·API·Git·AI 기초를 학습하는 개발 입문자 및 자기주도 학습자
- **목표:** 진단 결과에 기반한 계획 수립, 출처가 있는 AI 학습 코칭, 과제 및 진도 확인을 하나의 서비스에서 제공
- **활용 확장:** 해외 IT 교육생의 GitHub 기반 과제관리 및 멘토링 플랫폼으로 확장 가능 
### 1.4 차별성

1. 객관식 20문항과 서술형 2문항을 결합한 역량 진단
2. AI 생성 결과를 검증하고 실패 시 규칙 기반 계획으로 대체하는 안전한 설계
3. 출처가 표시되는 로컬 RAG 기반 학습 코칭
4. 사용자 본인의 학습 진도와 과제만 조회하도록 제한된 읽기 전용 Agent 도구

## 2. 팀원 및 역할

> 아래는 **3인 팀의 권장 역할 구분**입니다. 실제 담당자 이름과 GitHub 계정, 기여 근거는 최종 제출 전에 확인하여 기입하세요.

| 팀원   | 이름 / GitHub | 담당 역할(기입·수정)                   | 주요 산출물·기여 근거                                                                                                                                                                                       |
| ---- | ----------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 팀원 1 | **[박경부]**   | 프로젝트 총괄, Backend/API, 인증·DB·배포 | AI DevCoach의 프로젝트 구축과 통합 관리를 담당하고, 사용자 대시보드와 주요 화면 이동 체계를 구현하였다. AI Agent, RAG 기반 학습자료 검색, 학습계획 보강 기능을 개발하고, 학습통계 및 수준진단 기능의 오류 개선을 수행하였다. 또한 GitHub 브랜치와 Pull Request 기반의 협업 및 기능 통합을 담당하였다.      |
| 팀원 2 | **[류정민]**   | AI Agent, RAG, 서술형 평가, AI 학습계획 | Vercel 배포 설정과 Python 실행환경 구성을 담당하고, 이메일 기반 비밀번호 재설정 기능을 구현하였다. 완료 과제의 진도 저장 오류를 수정하고 배포 및 설치 안내를 README에 반영하여 시스템 운영 안정성과 재현성을 개선하였다. 사용자 피드백 정리 및 반영                                              |
| 팀원 3 | **[최석준]**   | Frontend, 화면 연계, 테스트·문서화       | GitHub 프로젝트 분석 기능과 분석 이력 관리 기능을 개발·통합하고, AI 학습 코칭의 대화 이력 저장 및 복원 기능을 개선하였다. Ruff, Black, ESLint를 활용한 코드 품질 검사 체계를 정비하고, AI 개발 지침 및 테스트 실행 절차를 문서화하였다. 자동 테스트 30개 통과 결과와 Pull Request 병합 증빙을 확보하였다. |
|      |             |                                |                                                                                                                                                                                                    |

- 협업 방식: 기능별 브랜치 → Pull Request → 코드 리뷰 → `main` 병합
- 팀원별 실제 기여도 증빙: **[작성 예정: PR 목록, Commit 이력, 담당 기능, 테스트 기록]**

- GitHub 기여 확인: [Repository contributors](https://github.com/bigpark61/AI_DevCoach/graphs/contributors) · [Pull requests](https://github.com/bigpark61/AI_DevCoach/pulls)

## 3. 주요 기능 및 구현 범위

아래는 구현된 기능 및 구현범위입니다. 

| 구분       | 기능                |      구현 설명                                         |
| -------- | ----------------- | -------------------------------------------------- |
| 계정·프로필   | 회원가입·로그인·비밀번호 재설정 | 이메일/비밀번호, 필수 동의, HttpOnly 세션 쿠키, 30분 만료 1회용 재설정 링크 |
| 학습자 관리   | 프로필 생성·수정         | 학습자 기본 정보 및 학습계획 입력에 활용                            |
| 역량 진단    | 22문항 평가           | 객관식 20 + 서술형 2, 중단 후 이어하기, 역량 피드백                  |
| AI 채점    | 서술형 평가            | 원인 이해 4점, 해결책 4점, 명확성 2점의 평가 기준을 이용한 AI 채점         |
| 학습계획     | 개인화 주간 계획         | 프로필·진단 결과 기반 초안 생성, 수정·검증·승인, 규칙 기반 대체 처리          |
| AI Coach | RAG 기반 질의응답       | 로컬 Markdown 검색, 출처 ID 표시, 학습 현황 및 과제 조회 도구         |
| 진도·과제    | 진행 정보 조회          | 사용자 범위가 제한된 진도·과제 조회 및 관리자 요약 대시보드                 |
| 운영       | 관리자 대시보드          | `ADMIN_EMAILS`에 등록된 계정만 관리자 API 접근 가능              |

## 4. 기술 스택

| 구분           | 기술                                  | 용도                      |
| ------------ | ----------------------------------- | ----------------------- |
| Backend      | Python 3.12+, FastAPI, Uvicorn      | REST API 및 서버 실행        |
| Frontend     | 웹 브라우저 기반 UI, JavaScript            | 사용자 화면 및 API 호출         |
| Database     | Neon PostgreSQL / 로컬 SQLite         | 사용자, 평가, 학습계획 및 활동 데이터  |
| DB Migration | Alembic                             | PostgreSQL 스키마 변경 관리    |
| LLM          | OpenAI API 호환 인터페이스                 | 서술형 채점, AI Coach, 계획 생성 |
| 기본 모델        | `gpt-4o-mini` (`OPENAI_MODEL` 기본값)  | 환경변수로 변경 가능             |
| Retrieval    | BM25, `backend/knowledge/` Markdown | 키워드 기반 관련 학습자료 검색       |
| 외부 연동        | 읽기 전용 Tool Calling                  | 학습자료 검색, 개인 진도·과제 조회    |
| 배포           | Vercel                              | 공개 웹 서비스 배포             |
| 코드 품질        | Ruff, Black, ESLint                 | 정적 검사·포맷 검증             |
| 테스트          | Python unittest, 컴파일 검사             | 자동 검증                   |
| 협업           | Git, GitHub, Pull Request           | 소스 관리 및 팀 협업            |

## 5. 시스템 아키텍처


![[AI DevCoach 시스템 아키텍처 흐름도.png]]


**설계 원칙**

- 브라우저에 LLM API 키나 DB 접속정보를 노출하지 않음
- 사용자 데이터 조회는 로그인한 사용자 범위로 제한
- AI 생성 학습계획은 검증 후 반영하며, 오류 시 규칙 기반 결과 유지
- DB 스키마 변경은 Alembic 마이그레이션으로 별도 수행


![[AI DevCoach 시스템 아키텍처 인포그래픽.png]]

## 6. 핵심 AI 기술

### 6.1 AI Agent 및 Tool Calling

**적용 목적:** 학습자의 질문을 이해하고, 필요한 학습자료나 본인의 진행 정보를 도구로 조회한 후 답변에 활용합니다.


![[AI DevCoach 학습 코칭 흐름.png]]


**중요:** 현재 도구는 **읽기 전용**이며 Agent가 계획이나 진도를 직접 수정하지 않습니다. 따라서 자율 실행형 Agent의 완성으로 보기는 어려운 상황입니다.

### 6.2 RAG 파이프라인

**적용 목적:** LLM의 일반 지식에만 의존하지 않고, 프로젝트가 제공하는 학습자료를 검색해 출처 기반 답변을 생성합니다.

![[AI DevCoach RAG 파이프라인 안내도.png]]

- **자료원:** `backend/knowledge/`의 선별된 Markdown 자료
- **검색 방식:** BM25 기반 어휘 검색(lexical retrieval)
- **생성 방식:** 검색 결과를 LLM 입력 문맥으로 전달
- **출처 처리:** 채팅 응답에 자료 출처 ID 표시
- **한계:** 임베딩·벡터DB 검색, 외부 문서 자동 수집은 현재 구현 범위가 아님

### 6.3 필수구현 기능 증빙

### **1. 필수 기술별 증빙 결과**

| 구분    | AI Agent             | RAG                    |
| ----- | -------------------- | ---------------------- |
| 핵심 기술 | LLM Tool Calling     | BM25 검색 증강 생성          |
| 구현 목적 | 개인별 학습진도 기반 코칭       | 학습자료 검색 및 근거 기반 답변     |
| 데이터   | 진도, 과제, 학습시간         | Markdown 학습자료          |
| 실행 증빙 | 진도 100%, 완료 과제 8개 인식 | `source_id` 및 참고 자료 표시 |
| 확인 결과 | 개인화 학습 상담 동작 확인      | 출처 포함 답변 동작 확인         |

### **AI Agent 증빙**

AI 코치가 학습자의 완료율 100%, 완료 과제 8개, 계획 학습시간 1,920분 및 실제 학습시간 1,100분을 인식하고 다음 학습 방향을 안내한 화면을 증빙으로 정리했습니다.

### **RAG 증빙**

AI 코치가 질문에 답변하면서 `[source_id: ai-agent-2]`와 관련 학습자료를 참고 문서로 표시한 실행 화면을 포함했습니다.

이는 단순 LLM 응답과 달리 **학습 지식베이스의 출처를 제시하는 기능**이 동작한다는 증거입니다.

![[AI Agent와 RAG 구현 증빙 infographics.png]]
### 6.4 AI 사용 범위와 안전장치

- 객관식은 정답표 비교, 서술형은 LLM 평가 기준 활용
- LLM 출력은 검증 후 사용하며 실패 시 규칙 기반 학습계획 유지
- API 키는 서버 측 환경변수로 관리
- AI 생성 내용은 오류가 있을 수 있으므로 학습자 확인 필요

## 7. 설치 및 실행

### 7.1 사전 준비

- Python **3.12 이상**
- Git
- 선택: `uv`, Node.js **24 이상 권장**(개발 품질 검사 시)
- 선택: Neon PostgreSQL 연결정보, OpenAI API 키, SMTP 정보

### 7.2 소스 내려받기

```powershell
git clone https://github.com/bigpark61/AI_DevCoach.git
cd AI_DevCoach
```

### 7.3 Windows PowerShell: 가상환경 및 설치

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 7.4 로컬 실행

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

또는 `uv` 사용 시:

```powershell
uv run --with-requirements requirements.txt uvicorn backend.main:app --reload
```

- 서비스: http://127.0.0.1:8000
- API 문서: http://127.0.0.1:8000/docs
- `DATABASE_URL` 미설정 시 로컬 SQLite `data/devcoach.db` 사용

### 7.5 환경변수

아래 값은 **설정 예시**이며 실제 인증정보를 README나 Git에 기록하지 마세요.

```dotenv
# PostgreSQL 운영 DB(미설정 시 로컬 SQLite 사용)
DATABASE_URL=postgresql://<user>:<password>@<pooled-host>/<database>
DATABASE_URL_UNPOOLED=postgresql://<user>:<password>@<direct-host>/<database>
COOKIE_SECURE=true

# AI
OPENAI_API_KEY=<your-secret-api-key>
OPENAI_MODEL=gpt-4o-mini
# OPENAI_BASE_URL=<optional-compatible-provider-url>

# 비밀번호 재설정 메일(필요 시)
APP_BASE_URL=https://<your-deployment-domain>
SMTP_HOST=<smtp-host>
SMTP_PORT=<smtp-port>
SMTP_FROM=<sender-email>
SMTP_USERNAME=<smtp-user>
SMTP_PASSWORD=<smtp-password>
SMTP_USE_SSL=false

# 관리자: 이미 가입된 계정의 이메일
ADMIN_EMAILS=<admin-email>
```

- `.env` 파일은 Git 추적 대상에서 제외해야 합니다.
- 운영 HTTPS에서는 `COOKIE_SECURE=true`를 사용합니다.
- 로컬 비밀번호 재설정 시험은 `PASSWORD_RESET_DEV_MODE=true`를 사용할 수 있으나 **운영 배포에서 금지**합니다.
- OpenAI API 키가 없으면 AI 채점·Agent 채팅은 설정 오류를 반환할 수 있습니다. 일부 규칙 기반 기능은 유지됩니다.

### 7.6 PostgreSQL 마이그레이션

`DATABASE_URL_UNPOOLED`에 직접 연결 문자열을 설정한 후:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

PostgreSQL 스키마는 서버 시작 시 자동 변경되지 않습니다. 첫 배포 및 스키마 변경 배포 전에 마이그레이션이 필요합니다.

### 7.7 코드 품질 및 자동 테스트

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
.\.venv\Scripts\python.exe scripts/check_quality.py
.\.venv\Scripts\python.exe scripts/check_quality.py --test
```

검사 스크립트는 소스를 자동 수정하지 않으며, Ruff·Black·ESLint와 `--test` 실행 시 unittest·Python 컴파일을 검사합니다. `npm run build`는 이 저장소에서 **프론트엔드 번들 빌드가 아니라 Python 백엔드 컴파일 검사**입니다.

## 8. 테스트 및 검증 결과

### 8.1 확인된 과거 검증 기록

| 일자 | 검증 항목 | 기록된 결과 | 비고 |
|---|---|---|---|
| 2026-11-15 | 로컬 Python 테스트 | **21 passed, 1 warning** | 당시 Windows PowerShell 실행 기록 |
| 2026-11-18 | Ruff·Black·ESLint, 컴파일 및 애플리케이션 테스트 | **30개 테스트 통과** | 기존 README의 검증 환경 기록 |
| 2026-11-18 | 캐시 헤더 관련 수정 | 검증 기록 문서 존재 | [`docs/testing/2026-11-18-cache-headers.md`](docs/testing/2026-11-18-cache-headers.md) |

- 상세 검사 가이드: [`docs/lint-guide-ko.md`](docs/lint-guide-ko.md)
- 위 결과는 **당시 기록**이며, 현재 `main`을 새로 설치한 환경이나 운영 배포의 통과를 자동 보장하지 않습니다.


## 9. 실사용자 테스트 및 피드백

### 9.1 테스트 개요

| 항목 | 입력란 |
|---|---|
| 테스트 목적 | 회원가입, 수준진단, 계획 생성, AI Coach 사용성 및 신뢰성 검증 |
| 테스트 기간 | **[YYYY-MM-DD ~ YYYY-MM-DD]** |
| 테스트 인원 | **[실제 인원: 최소 5명 이상 권장]** |
| 대상 사용자 | **[학습자 유형·선정 기준]** |
| 테스트 환경 | **[배포 URL·브라우저·기기]** |
| 조사 방법 | **[실사용 관찰 / 설문 / 인터뷰]** |
| 개인정보 처리 | 익명 ID 사용, 필요한 동의 확보, 민감정보·비밀번호 수집 금지 |

### 9.2 사용자 피드백 

사용자 피드백은 아래 별도 문서로 제출함
사용자 20명 등록, 5명에 대한 심층의견 접수 및 분석

[[사용자 피드백 정리]]

## 10. 배포 및 관련 링크

| 항목            | 링크                                         | 상태                                  |
| ------------- | ------------------------------------------ | ----------------------------------- |
| GitHub 저장소    | https://github.com/bigpark61/AI_DevCoach   | 주소 확인                               |
| 공개 서비스        | https://ai-dev-coach.vercel.app            | 기존 README에 기재됨, **현재 접속·동작 재확인 필요** |
| API 상태 확인     | https://ai-dev-coach.vercel.app/api/health | **실제 응답 확인 필요**                     |
| API 문서(로컬)    | http://127.0.0.1:8000/docs                 | 로컬 실행 시 확인                          |
| 프로젝트 기획서      | **[GitHub `/docs` 프로젝트기획안]**               | 작성 완료                               |
| 기능 요구사항 명세서   | **[GitHub `/docs` 기능모듈설계서]**               | 작성 완료                               |
| 사용자 피드백·개선 결과 | **[GitHub `/docs` 사용자피드백]**                | 작성 완료                               |
| 평가자 테스트 계정    | **[별도 안전한 전달 경로 기입]**                      | 작성 완료                               |

> 테스트 계정의 실제 비밀번호는 공개 README에 적지 마세요.

## 11. 보안·개인정보 및 AI 사용 고지

- 비밀번호는 서버에서 PBKDF2 해싱하여 관리하며, 세션은 HttpOnly 쿠키를 사용한다고 기존 README에 명시되어 있습니다.
- 비밀번호 재설정 토큰은 1회용·30분 만료이며 변경 후 기존 세션을 무효화합니다.
- 필수 개인정보 동의 기록을 수집하며, **실제 동의 문구·보관기간·삭제 절차는 최종 확인 필요**합니다.
- API 키, SMTP 비밀번호, DB 연결 문자열은 `.env` 또는 배포 서비스의 비밀 환경변수에 저장합니다.
- AI가 생성한 서술형 평가·학습계획·코칭 답변은 **AI 생성 결과**임을 사용자에게 명확히 알리는 UI가 있는지 **확인 필요**합니다.
- AI Coach의 Tool Calling은 로그인 사용자 본인 정보 조회로 제한하며, 학습계획·진도 변경 권한은 부여하지 않습니다.
- 이메일 주소 자체 검증(email verification)은 현재 MVP에서 제공되지 않습니다.

## 12. 제출 전 점검표 

### 12.1 제출 전 점검표

- [ ] 팀원 3명의 실제 이름, 역할, GitHub 기여 증빙 확정
- [ ] 기획서·요구사항 명세서·발표자료·피드백 문서를 `/docs`에 정리
- [ ] 배포 서비스와 `/api/health` 직접 접속 검증
- [ ] 데이터베이스 마이그레이션 및 테스트 계정 확인
- [ ] AI Agent 도구 호출 화면·로그 캡처
- [ ] RAG 검색 결과와 실제 출처 문서 대응 검증
- [ ] Long-term Memory로 주장할 이력 저장·재조회·활용 범위 명확화
- [ ] 필수 기능 E2E 테스트 실행 및 결과 캡처
- [ ] **실사용자 5명 이상** 테스트·피드백·개선·재검증 증빙 작성
- [ ] 개인정보 동의, AI 생성물 고지, 비밀정보 노출 여부 점검
- [ ] 현재 `main` 기준 품질 검사 재실행

