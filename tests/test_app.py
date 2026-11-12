import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from unittest.mock import Mock, patch

import httpx
from openai import OpenAI
from fastapi.testclient import TestClient

from backend.main import (
    QUESTIONS,
    PlanGenerateInput,
    _build_grounded_plan,
    _grade_written_with_openai,
    _validate_plan,
    create_app,
)
from backend.agent import run_learning_agent
from backend.ai_client import configured_model, create_ai_client
from backend.knowledge import search_knowledge


class DevCoachFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        app = create_app(Path(self.temp_dir.name) / "test.db")
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.temp_dir.cleanup()

    def signup(self, email="learner@example.com"):
        return self.client.post(
            "/api/auth/signup",
            json={
                "email": email,
                "password": "correct-horse-42",
                "terms_agreed": True,
                "privacy_agreed": True,
            },
        )

    def profile(self):
        return self.client.post(
            "/api/profiles",
            json={
                "nickname": "Learner",
                "learning_goal": "AI Agent 웹서비스 개발",
                "self_assessed_level": "beginner",
                "interest_skills": ["Python", "FastAPI"],
                "weekly_hours": 8,
                "duration_weeks": 4,
                "github_username": "",
                "learning_notes": "",
            },
        )

    def test_registration_requires_consent_and_duplicate_email_is_rejected(self):
        missing_consent = self.client.post(
            "/api/auth/signup",
            json={
                "email": "learner@example.com",
                "password": "correct-horse-42",
                "terms_agreed": True,
                "privacy_agreed": False,
            },
        )
        self.assertEqual(missing_consent.status_code, 400)
        self.assertEqual(self.signup().status_code, 201)
        self.assertEqual(self.signup().status_code, 409)

    def test_login_and_logout_manage_the_session_cookie(self):
        self.signup()
        logout = self.client.post("/api/auth/logout")
        self.assertEqual(logout.status_code, 204)
        invalid = self.client.post(
            "/api/auth/login",
            json={"email": "learner@example.com", "password": "incorrect-password"},
        )
        self.assertEqual(invalid.status_code, 401)
        login = self.client.post(
            "/api/auth/login",
            json={"email": "learner@example.com", "password": "correct-horse-42"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("httponly", login.headers["set-cookie"].lower())
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        logout = self.client.post("/api/auth/logout")
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_profile_patch_requires_existing_profile(self):
        self.signup()
        response = self.client.patch(
            "/api/profiles/me",
            json={
                "nickname": "Learner",
                "learning_goal": "AI Agent 웹서비스 개발",
                "self_assessed_level": "beginner",
                "interest_skills": ["Python", "FastAPI"],
                "weekly_hours": 8,
                "duration_weeks": 4,
                "github_username": "",
                "learning_notes": "",
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "학습 프로필을 먼저 등록해 주세요.")

    def test_admin_overview_is_restricted_to_allowlisted_emails(self):
        self.assertEqual(self.client.get("/api/admin/overview").status_code, 401)
        self.signup("admin@example.com")
        with patch.dict(
            os.environ, {"ADMIN_EMAILS": "ADMIN@example.com, other@example.com"}
        ):
            self.assertTrue(self.client.get("/api/auth/me").json()["is_admin"])
            overview = self.client.get("/api/admin/overview")
        self.assertEqual(overview.status_code, 200, overview.text)
        self.assertEqual(overview.json()["user_count"], 1)
        self.assertEqual(overview.json()["users"][0]["email"], "admin@example.com")
        self.assertEqual(overview.json()["users"][0]["tasks"], [])

        self.client.post("/api/auth/logout")
        self.signup("learner@example.com")
        with patch.dict(os.environ, {"ADMIN_EMAILS": "admin@example.com"}):
            denied = self.client.get("/api/admin/overview")
        self.assertEqual(denied.status_code, 403)

    def test_agent_chat_requires_authentication_and_ai_provider(self):
        provider_env = {
            "OPENAI_API_KEY": "",
            "OPENAI_BASE_URL": "",
            "NEON_AI_GATEWAY_TOKEN": "",
            "NEON_AI_GATEWAY_BASE_URL": "",
        }
        with patch.dict(os.environ, provider_env):
            unauthenticated = self.client.post(
                "/api/agent/chat", json={"message": "RAG를 설명해 줘"}
            )
            self.assertEqual(unauthenticated.status_code, 401)
            self.signup("agent-learner@example.com")
            unavailable = self.client.post(
                "/api/agent/chat", json={"message": "RAG를 설명해 줘"}
            )
        self.assertEqual(unavailable.status_code, 503)
        self.assertIn("AI 코치 설정", unavailable.json()["detail"])

    def test_knowledge_search_returns_relevant_citable_sources(self):
        results = search_knowledge("RAG 검색 출처 근거")
        self.assertTrue(results)
        self.assertEqual(results[0]["source_id"], "rag-fundamentals-1")
        self.assertIn("검색 결과", results[0]["content"])
        self.assertEqual(search_knowledge("xylophonezzqv"), [])

    def test_agent_uses_read_only_tool_then_returns_grounded_answer(self):
        tool_call = SimpleNamespace(
            id="call-search",
            function=SimpleNamespace(
                name="search_learning_resources",
                arguments=json.dumps({"query": "RAG source citation"}),
            ),
        )
        tool_message = SimpleNamespace(
            tool_calls=[tool_call],
            model_dump=lambda **kwargs: {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call-search",
                        "type": "function",
                        "function": {
                            "name": "search_learning_resources",
                            "arguments": tool_call.function.arguments,
                        },
                    }
                ],
            },
        )
        final_message = SimpleNamespace(
            tool_calls=[],
            content="RAG는 검색 결과를 근거로 답합니다. [rag-fundamentals-1]",
        )
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        side_effect=[
                            SimpleNamespace(
                                choices=[SimpleNamespace(message=tool_message)]
                            ),
                            SimpleNamespace(
                                choices=[SimpleNamespace(message=final_message)]
                            ),
                        ]
                    )
                )
            )
        )
        search_handler = Mock(
            return_value={"results": [{"source_id": "rag-fundamentals-1"}]}
        )

        result = run_learning_agent(
            client=client,
            model="test-model",
            message="RAG가 뭔가요?",
            history=[],
            handlers={"search_learning_resources": search_handler},
        )

        search_handler.assert_called_once_with({"query": "RAG source citation"})
        self.assertIn("[rag-fundamentals-1]", result["reply"])
        self.assertEqual(result["tool_calls"], ["search_learning_resources"])

    def test_agent_chat_returns_only_retrieved_citations(self):
        self.signup("rag-learner@example.com")
        tool_call = SimpleNamespace(
            id="call-search",
            function=SimpleNamespace(
                name="search_learning_resources",
                arguments=json.dumps({"query": "RAG 검색 출처 근거"}),
            ),
        )
        tool_message = SimpleNamespace(
            tool_calls=[tool_call],
            model_dump=lambda **kwargs: {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call-search",
                        "type": "function",
                        "function": {
                            "name": "search_learning_resources",
                            "arguments": tool_call.function.arguments,
                        },
                    }
                ],
            },
        )
        final_message = SimpleNamespace(
            tool_calls=[],
            content="관련 자료를 확인했습니다. [rag-fundamentals-1] [unknown-source]",
        )
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        side_effect=[
                            SimpleNamespace(
                                choices=[SimpleNamespace(message=tool_message)]
                            ),
                            SimpleNamespace(
                                choices=[SimpleNamespace(message=final_message)]
                            ),
                        ]
                    )
                )
            )
        )
        with patch("backend.main.create_ai_client", return_value=client):
            response = self.client.post(
                "/api/agent/chat", json={"message": "RAG 출처 근거는?"}
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("[rag-fundamentals-1]", response.json()["reply"])
        self.assertNotIn("unknown-source", response.json()["reply"])
        self.assertEqual(
            response.json()["sources"][0]["source_id"], "rag-fundamentals-1"
        )

    def test_ai_client_prefers_neon_gateway_credentials(self):
        with patch.dict(
            os.environ,
            {
                "NEON_AI_GATEWAY_TOKEN": "gateway-test-token",
                "NEON_AI_GATEWAY_BASE_URL": "https://branch-api.ai.example",
                "OPENAI_API_KEY": "fallback-test-key",
                "AI_MODEL": "catalog-model",
                "OPENAI_MODEL": "fallback-model",
            },
        ), patch("backend.ai_client.OpenAI") as openai_client:
            create_ai_client()
            self.assertEqual(configured_model(), "catalog-model")
        openai_client.assert_called_once_with(
            api_key="gateway-test-token",
            base_url="https://branch-api.ai.example/v1",
            timeout=30.0,
            max_retries=1,
        )

    def test_grounded_plan_uses_sources_without_changing_schedule(self):
        payload = PlanGenerateInput(
            goal="RAG 학습 코치 만들기",
            duration_weeks=4,
            weekly_hours=8,
            difficulty="balanced",
            learning_style="project",
            focus_skills=["LLM·AI Agent 활용"],
            additional_requirements="검색 출처 표시",
        )
        generated_weeks = []
        for week_no in range(1, 5):
            generated_weeks.append(
                {
                    "week_no": week_no,
                    "weekly_goal": f"{week_no}주차 RAG 실습 목표",
                    "tasks": [
                        {
                            "title": f"{week_no}주차 과제 {task_no}",
                            "deliverable": "검증 가능한 구현 결과",
                            "completion_criteria": "테스트와 출처 표시를 확인",
                            "resource_ids": ["rag-fundamentals-1", "invented-source"],
                        }
                        for task_no in range(1, 3)
                    ],
                }
            )
        generated_json = json.dumps({"weeks": generated_weeks}, ensure_ascii=False)
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content=generated_json)
                                )
                            ]
                        ),
                    )
                )
            )
        )
        with patch("backend.main.create_ai_client", return_value=client), patch(
            "backend.main.search_knowledge",
            return_value=[
                {
                    "source_id": "rag-fundamentals-1",
                    "title": "RAG 학습자료: 검색 증강 생성 흐름",
                    "content": "...",
                }
            ],
        ):
            plan = _build_grounded_plan(
                payload,
                {"self_assessed_level": "beginner", "interest_skills": ["RAG"]},
                {"skill_scores": {"LLM·AI Agent 활용": 52}},
            )

        self.assertEqual(plan["generated_by"], "retrieval_augmented_ai")
        self.assertEqual(plan["source_ids"], ["rag-fundamentals-1"])
        self.assertEqual(len(plan["weeks"]), 4)
        self.assertEqual(plan["weeks"][0]["tasks"][0]["estimated_hours"], 4)
        self.assertEqual(
            plan["weeks"][0]["tasks"][0]["learning_resources"],
            [
                "[rag-fundamentals-1] RAG 학습자료: 검색 증강 생성 흐름",
            ],
        )
        self.assertTrue(
            all(
                sum(task["estimated_hours"] for task in week["tasks"]) <= 8
                for week in plan["weeks"]
            )
        )
        self.assertEqual(_validate_plan(plan), [])

    def test_invalid_ai_plan_falls_back_to_rules(self):
        payload = PlanGenerateInput(
            goal="AI Agent 학습",
            duration_weeks=4,
            weekly_hours=6,
            difficulty="foundation",
            learning_style="examples",
            focus_skills=["LLM·AI Agent 활용"],
        )
        invalid_weeks = []
        for week_no in range(1, 5):
            invalid_weeks.append(
                {
                    "week_no": week_no,
                    "weekly_goal": f"AI 주차 {week_no}",
                    "tasks": [
                        {
                            "title": f"AI 과제 {week_no}-{task_no}",
                            "deliverable": "결과물",
                            "completion_criteria": "테스트 통과",
                            "resource_ids": [
                                (
                                    "not-in-retrieved-sources"
                                    if week_no == 4 and task_no == 2
                                    else "ai-agent-1"
                                )
                            ],
                        }
                        for task_no in range(1, 3)
                    ],
                }
            )
        invalid_json = json.dumps({"weeks": invalid_weeks}, ensure_ascii=False)
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content=invalid_json)
                                )
                            ]
                        ),
                    )
                )
            )
        )
        with patch("backend.main.create_ai_client", return_value=client), patch(
            "backend.main.search_knowledge",
            return_value=[
                {"source_id": "ai-agent-1", "title": "Agent", "content": "..."}
            ],
        ):
            plan = _build_grounded_plan(
                payload,
                {"self_assessed_level": "beginner", "interest_skills": []},
                {"skill_scores": {}},
            )

        self.assertEqual(plan["generated_by"], "규칙 기반 개인화 플래너")
        self.assertNotIn("source_ids", plan)
        self.assertNotIn("AI 과제", plan["weeks"][0]["tasks"][0]["title"])
        self.assertNotIn("AI 주차", plan["weeks"][0]["weekly_goal"])
        self.assertEqual(_validate_plan(plan), [])

    def test_password_reset_changes_password_once_and_revokes_sessions(self):
        self.signup()
        with patch.dict(
            os.environ,
            {
                "APP_BASE_URL": "http://testserver",
                "SMTP_HOST": "smtp.example.com",
                "SMTP_FROM": "coach@example.com",
                "COOKIE_SECURE": "false",
                "PASSWORD_RESET_DEV_MODE": "false",
            },
        ), patch("backend.main._send_password_reset_email") as send_email:
            requested = self.client.post(
                "/api/auth/password-reset-requests",
                json={"email": "learner@example.com"},
            )
        self.assertEqual(requested.status_code, 200)
        self.assertEqual(send_email.call_count, 1)
        reset_url = send_email.call_args.args[1]
        token = parse_qs(urlparse(reset_url).fragment)["reset_token"][0]

        changed = self.client.post(
            "/api/auth/password-resets",
            json={"token": token, "password": "new-secure-password"},
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        reused = self.client.post(
            "/api/auth/password-resets",
            json={"token": token, "password": "another-password"},
        )
        self.assertEqual(reused.status_code, 400)
        old_login = self.client.post(
            "/api/auth/login",
            json={"email": "learner@example.com", "password": "correct-horse-42"},
        )
        self.assertEqual(old_login.status_code, 401)
        new_login = self.client.post(
            "/api/auth/login",
            json={"email": "learner@example.com", "password": "new-secure-password"},
        )
        self.assertEqual(new_login.status_code, 200)

    def test_password_reset_request_hides_account_existence(self):
        self.signup()
        with patch.dict(
            os.environ,
            {
                "APP_BASE_URL": "http://testserver",
                "SMTP_HOST": "smtp.example.com",
                "SMTP_FROM": "coach@example.com",
                "COOKIE_SECURE": "true",
                "PASSWORD_RESET_DEV_MODE": "true",
            },
        ), patch("backend.main._send_password_reset_email") as send_email:
            known = self.client.post(
                "/api/auth/password-reset-requests",
                json={"email": "learner@example.com"},
            )
            unknown = self.client.post(
                "/api/auth/password-reset-requests",
                json={"email": "missing@example.com"},
            )
        self.assertEqual(known.json(), unknown.json())
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(send_email.call_count, 1)

    def test_password_reset_dev_link_is_only_returned_when_enabled_for_local_http(self):
        self.signup()
        with patch.dict(
            os.environ,
            {
                "APP_BASE_URL": "",
                "COOKIE_SECURE": "false",
                "PASSWORD_RESET_DEV_MODE": "true",
            },
            clear=False,
        ):
            response = self.client.post(
                "/api/auth/password-reset-requests",
                json={"email": "learner@example.com"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            urlparse(response.json()["dev_reset_url"]).netloc, "testserver"
        )

    def test_profile_validation_and_authentication(self):
        self.assertEqual(self.client.get("/api/profiles/me").status_code, 401)
        self.signup()
        invalid = self.client.post(
            "/api/profiles",
            json={
                "nickname": " ",
                "learning_goal": "goal",
                "self_assessed_level": "beginner",
                "interest_skills": [],
                "weekly_hours": 41,
                "duration_weeks": 4,
                "github_username": "",
                "learning_notes": "",
            },
        )
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(self.profile().status_code, 201)
        self.assertEqual(self.client.get("/api/profiles/me").json()["weekly_hours"], 8)

    def test_github_analysis_collects_public_evidence_and_saves_private_history(self):
        self.signup()

        def fake_github_get(_client, path, **kwargs):
            if path == "/repos/learner/demo":
                return {
                    "id": 12,
                    "full_name": "learner/demo",
                    "description": "A demo project",
                    "html_url": "https://github.com/learner/demo",
                    "default_branch": "main",
                    "private": False,
                    "stargazers_count": 2,
                    "updated_at": "2026-10-25T00:00:00Z",
                }
            if path.endswith("/branches/main"):
                return {"commit": {"sha": "abc123456789"}}
            if "/git/trees/" in path:
                return {
                    "truncated": False,
                    "tree": [
                        {"path": "README.md", "type": "blob", "size": 200},
                        {"path": "main.py", "type": "blob", "size": 80},
                        {"path": "tests/test_main.py", "type": "blob", "size": 40},
                    ],
                }
            if path.endswith("/readme"):
                readme = "# Demo\n\n## Features\n\n## Tech Stack\n\n## Installation and Usage\n\n## Environment Variables\n\n## API example\n\n## Tests\n\nAPI_KEY=demo-secret-value-123456"
                return {
                    "encoding": "base64",
                    "content": base64.b64encode(readme.encode()).decode(),
                }
            if path.endswith("/languages"):
                return {"Python": 500}
            if path.endswith("/commits"):
                return [
                    {
                        "sha": "abc123456789",
                        "html_url": "https://github.com/learner/demo/commit/abc123",
                        "commit": {
                            "message": "Add demo API",
                            "author": {
                                "name": "Learner",
                                "date": "2026-10-25T00:00:00Z",
                            },
                        },
                    }
                ]
            if "/contents/" in path:
                return {
                    "encoding": "base64",
                    "content": base64.b64encode(b"def app(): return True").decode(),
                }
            self.fail(f"Unexpected GitHub API path: {path} {kwargs}")

        with patch("backend.main._github_get", side_effect=fake_github_get), patch.dict(
            os.environ, {"OPENAI_API_KEY": ""}
        ):
            response = self.client.post(
                "/api/github/analyses",
                json={
                    "repo_url": "https://github.com/learner/demo",
                    "task_criteria": "Add API routes",
                },
            )
        self.assertEqual(response.status_code, 201, response.text)
        result = response.json()
        self.assertEqual(result["commit_sha"], "abc123456789")
        self.assertEqual(result["analysis_source"], "rules")
        self.assertEqual(result["tech_stack"], ["Python"])
        self.assertTrue(result["readme"]["present"])
        self.assertNotIn("demo-secret-value-123456", result["readme"]["excerpt"])
        self.assertIn("[REDACTED]", result["readme"]["excerpt"])
        self.assertEqual(
            result["analyzed_source_files"], ["main.py", "tests/test_main.py"]
        )
        self.assertEqual(result["review"]["task_verification"], "needs_review")
        self.assertEqual(
            self.client.get("/api/github/analyses").json()[0]["id"], result["id"]
        )
        self.assertEqual(
            self.client.get(f"/api/github/analyses/{result['id']}").json()[
                "commit_sha"
            ],
            result["commit_sha"],
        )

        self.client.post("/api/auth/logout")
        self.signup("other@example.com")
        self.assertEqual(
            self.client.get(f"/api/github/analyses/{result['id']}").status_code, 404
        )
        self.assertEqual(self.client.get("/api/github/analyses").json(), [])

    def test_github_analysis_rejects_non_repository_urls_before_api_access(self):
        self.signup()
        with patch("backend.main._github_get") as github_get:
            response = self.client.post(
                "/api/github/analyses",
                json={"repo_url": "https://example.com/owner/repo"},
            )
        self.assertEqual(response.status_code, 422)
        github_get.assert_not_called()

    def test_assessment_saves_resumes_scores_and_personalizes_plan(self):
        self.signup()
        self.profile()
        no_result = self.client.get("/api/assessments/latest")
        self.assertEqual(no_result.status_code, 404)
        self.assertEqual(no_result.json()["detail"], "완료된 수준 진단이 없습니다.")
        questions = self.client.get("/api/assessments/questions").json()["questions"]
        self.assertEqual(len(questions), 22)
        self.assertNotIn("answer", questions[0])
        session = self.client.post("/api/assessments/start").json()
        for question in questions:
            answer = (
                question["options"][0]["id"]
                if question["type"] == "objective"
                else "빈 목록인지 확인하고 예외 처리를 합니다."
            )
            saved = self.client.patch(
                f"/api/assessments/{session['id']}/answers",
                json={"question_id": question["id"], "answer": answer},
            )
            self.assertEqual(saved.status_code, 200)
        self.assertTrue(self.client.post("/api/assessments/start").json()["resumed"])
        with patch(
            "backend.main._grade_written_with_openai",
            return_value=(7, ["AI 루브릭 평가"]),
        ) as grader:
            result = self.client.post(f"/api/assessments/{session['id']}/submit")
        self.assertEqual(grader.call_count, 2)
        self.assertEqual(result.status_code, 200)
        self.assertGreater(result.json()["total_score"], 0)
        self.assertEqual(result.json()["skill_scores"]["코드 이해·오류 분석"], 70)
        self.assertEqual(
            self.client.post(f"/api/assessments/{session['id']}/submit").json()[
                "total_score"
            ],
            result.json()["total_score"],
        )
        latest = self.client.get("/api/assessments/latest")
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(latest.json()["id"], session["id"])

        plan = self.client.post(
            "/api/plans/generate",
            json={
                "goal": "FastAPI 기반 AI 학습 서비스",
                "duration_weeks": 4,
                "weekly_hours": 8,
                "difficulty": "balanced",
                "learning_style": "project",
                "focus_skills": ["API·데이터 처리"],
                "additional_requirements": "",
            },
        )
        self.assertEqual(plan.status_code, 201, plan.text)
        plan_data = plan.json()
        self.assertEqual(len(plan_data["weeks"]), 4)
        self.assertTrue(
            all(
                sum(task["estimated_hours"] for task in week["tasks"]) <= 8
                for week in plan_data["weeks"]
            )
        )
        self.assertTrue(
            self.client.post(f"/api/plans/{plan_data['id']}/validate").json()["valid"]
        )
        self.assertEqual(
            self.client.get("/api/plans/current").json()["status"], "draft"
        )
        approved = self.client.post(f"/api/plans/{plan_data['id']}/approve")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(
            self.client.get("/api/plans/current").json()["status"], "approved"
        )

        progress = self.client.get("/api/progress/dashboard")
        self.assertEqual(progress.status_code, 200, progress.text)
        self.assertEqual(progress.json()["total_tasks"], 8)
        self.assertEqual(progress.json()["completion_rate"], 0)
        task_id = "w1-t1"
        started = self.client.patch(
            f"/api/tasks/{task_id}",
            json={
                "status": "in_progress",
                "learning_notes": "API 요청을 구현했습니다.",
            },
        )
        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["status"], "in_progress")
        self.assertTrue(started.json()["learning_start_date"])
        time_log = self.client.post(
            f"/api/tasks/{task_id}/time-logs",
            json={
                "learning_date": "2026-10-24",
                "duration_minutes": 60,
                "notes": "요청 처리 실습",
            },
        )
        self.assertEqual(time_log.status_code, 201, time_log.text)
        time_edit = self.client.patch(
            f"/api/tasks/{task_id}/time-logs/{time_log.json()['id']}",
            json={
                "learning_date": "2026-10-24",
                "duration_minutes": 75,
                "notes": "오류 처리까지 실습",
            },
        )
        self.assertEqual(time_edit.status_code, 200, time_edit.text)
        self.assertEqual(time_edit.json()["duration_minutes"], 75)
        submission = self.client.post(
            f"/api/tasks/{task_id}/submissions",
            json={
                "github_url": "https://github.com/learner/project",
                "explanation": "기능 구현 결과",
            },
        )
        self.assertEqual(submission.status_code, 201, submission.text)
        self.assertEqual(
            self.client.post(
                f"/api/tasks/{task_id}/completion-request",
                json={"completion_criteria_confirmed": False},
            ).status_code,
            422,
        )
        completed = self.client.post(
            f"/api/tasks/{task_id}/completion-request",
            json={"completion_criteria_confirmed": True},
        )
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(completed.json()["status"], "completed")
        dashboard = self.client.get("/api/progress/dashboard").json()
        self.assertEqual(dashboard["completed_tasks"], 1)
        self.assertEqual(dashboard["actual_minutes"], 75)
        self.assertEqual(dashboard["weeks"][0]["completed_tasks"], 1)
        with patch.dict(os.environ, {"ADMIN_EMAILS": "learner@example.com"}):
            admin_user = self.client.get("/api/admin/overview").json()["users"][0]
        self.assertEqual(admin_user["total_tasks"], 8)
        self.assertEqual(admin_user["completed_tasks"], 1)
        self.assertEqual(admin_user["actual_minutes"], 75)
        self.assertEqual(
            admin_user["tasks"][0]["submission_url"],
            "https://github.com/learner/project",
        )
        self.assertEqual(
            len(self.client.get(f"/api/tasks/{task_id}/time-logs").json()), 1
        )
        statistics = self.client.get("/api/progress/statistics")
        self.assertEqual(statistics.status_code, 200, statistics.text)
        self.assertEqual(statistics.json()["completion_rate"], 12)
        activities = self.client.get("/api/progress/activities")
        self.assertEqual(activities.status_code, 200, activities.text)
        self.assertEqual(activities.json()[0]["event_type"], "task_completed")
        self.assertIn(
            "time_log_updated",
            [activity["event_type"] for activity in activities.json()],
        )
        coaching = self.client.post("/api/coach/progress-feedback")
        self.assertEqual(coaching.status_code, 200, coaching.text)
        self.assertEqual(coaching.json()["source"], "record_based_rules")
        revision = self.client.post(
            f"/api/plans/{plan_data['id']}/revision-request",
            json={"reason": "주당 학습 가능 시간이 변경되었습니다."},
        )
        self.assertEqual(revision.status_code, 201, revision.text)

    def test_plan_approval_blocks_over_budget_and_other_user_cannot_read(self):
        self.signup()
        self.profile()
        questions = self.client.get("/api/assessments/questions").json()["questions"]
        session = self.client.post("/api/assessments/start").json()
        for question in questions:
            if question["type"] == "objective":
                self.client.patch(
                    f"/api/assessments/{session['id']}/answers",
                    json={
                        "question_id": question["id"],
                        "answer": question["options"][0]["id"],
                    },
                )
        self.client.post(f"/api/assessments/{session['id']}/submit")
        plan = self.client.post(
            "/api/plans/generate",
            json={
                "goal": "서비스 개발",
                "duration_weeks": 4,
                "weekly_hours": 2,
                "difficulty": "foundation",
                "learning_style": "examples",
                "focus_skills": [],
                "additional_requirements": "",
            },
        ).json()
        plan["weeks"][0]["tasks"][0]["estimated_hours"] = 3
        invalid = self.client.patch(f"/api/plans/{plan['id']}", json={"plan": plan})
        self.assertEqual(invalid.status_code, 422)
        self.client.post("/api/auth/logout")
        self.signup("other@example.com")
        self.assertEqual(self.client.get(f"/api/plans/{plan['id']}").status_code, 404)

    def test_question_bank_shape(self):
        self.assertEqual(len(QUESTIONS), 22)
        objective = [q for q in QUESTIONS if q["type"] == "objective"]
        self.assertEqual(len(objective), 20)
        self.assertEqual(len({q["category"] for q in QUESTIONS}), 5)

    def test_written_grader_uses_openai_structured_rubric(self):
        content = json.dumps(
            {
                "root_cause_score": 4,
                "root_cause_evidence": "빈 목록에서 첫 항목을 요청하면 인덱스 오류가 발생합니다.",
                "solution_score": 3,
                "solution_evidence": "빈 목록 여부를 먼저 확인하라고 제안했습니다.",
                "clarity_score": 1,
                "clarity_evidence": "설명은 간결하지만 예외 처리 설명은 없습니다.",
                "feedback": "입력 검증을 추가하고 예외 처리 결과도 명시해 보세요.",
            }
        )
        requests = []

        def handle_request(request):
            requests.append(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-test",
                    "object": "chat.completion",
                    "created": 1,
                    "model": "gpt-4o-mini",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": content},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )

        with httpx.Client(transport=httpx.MockTransport(handle_request)) as http_client:
            client = OpenAI(api_key="test-key", http_client=http_client)
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch(
                "backend.ai_client.OpenAI", return_value=client
            ):
                score, feedback = _grade_written_with_openai(
                    QUESTIONS[21], "빈 목록인지 확인하고 예외를 처리합니다."
                )
        self.assertEqual(score, 8)
        self.assertEqual(len(feedback), 4)
        self.assertEqual(requests[0]["model"], "gpt-4o-mini")
        self.assertEqual(requests[0]["response_format"]["json_schema"]["strict"], True)
        self.assertIn(
            "빈 목록인지 확인하고 예외를 처리합니다.",
            requests[0]["messages"][1]["content"],
        )

    def test_missing_openai_key_preserves_answers_and_allows_retry(self):
        self.signup()
        self.profile()
        session = self.client.post("/api/assessments/start").json()
        saved = self.client.patch(
            f"/api/assessments/{session['id']}/answers",
            json={
                "question_id": "q21",
                "answer": "네트워크 오류와 응답 상태를 확인합니다.",
            },
        )
        self.assertEqual(saved.status_code, 200)
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            failed = self.client.post(f"/api/assessments/{session['id']}/submit")
        self.assertEqual(failed.status_code, 503)
        self.assertIn("OPENAI_API_KEY", failed.json()["detail"])
        resumed = self.client.get(f"/api/assessments/{session['id']}")
        self.assertEqual(resumed.json()["status"], "in_progress")
        self.assertEqual(
            resumed.json()["answers"]["q21"], "네트워크 오류와 응답 상태를 확인합니다."
        )


if __name__ == "__main__":
    unittest.main()
