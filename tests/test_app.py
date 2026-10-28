import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from openai import OpenAI
from fastapi.testclient import TestClient

from backend.main import QUESTIONS, _grade_written_with_openai, create_app


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
                    "id": 12, "full_name": "learner/demo", "description": "A demo project",
                    "html_url": "https://github.com/learner/demo", "default_branch": "main",
                    "private": False, "stargazers_count": 2, "updated_at": "2026-10-25T00:00:00Z",
                }
            if path.endswith("/branches/main"):
                return {"commit": {"sha": "abc123456789"}}
            if "/git/trees/" in path:
                return {"truncated": False, "tree": [
                    {"path": "README.md", "type": "blob", "size": 200},
                    {"path": "main.py", "type": "blob", "size": 80},
                    {"path": "tests/test_main.py", "type": "blob", "size": 40},
                ]}
            if path.endswith("/readme"):
                readme = "# Demo\n\n## Features\n\n## Tech Stack\n\n## Installation and Usage\n\n## Environment Variables\n\n## API example\n\n## Tests\n\nAPI_KEY=demo-secret-value-123456"
                return {"encoding": "base64", "content": base64.b64encode(readme.encode()).decode()}
            if path.endswith("/languages"):
                return {"Python": 500}
            if path.endswith("/commits"):
                return [{"sha": "abc123456789", "html_url": "https://github.com/learner/demo/commit/abc123", "commit": {
                    "message": "Add demo API", "author": {"name": "Learner", "date": "2026-10-25T00:00:00Z"},
                }}]
            if "/contents/" in path:
                return {"encoding": "base64", "content": base64.b64encode(b"def app(): return True").decode()}
            self.fail(f"Unexpected GitHub API path: {path} {kwargs}")

        with patch("backend.main._github_get", side_effect=fake_github_get), patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            response = self.client.post(
                "/api/github/analyses",
                json={"repo_url": "https://github.com/learner/demo", "task_criteria": "Add API routes"},
            )
        self.assertEqual(response.status_code, 201, response.text)
        result = response.json()
        self.assertEqual(result["commit_sha"], "abc123456789")
        self.assertEqual(result["analysis_source"], "rules")
        self.assertEqual(result["tech_stack"], ["Python"])
        self.assertTrue(result["readme"]["present"])
        self.assertNotIn("demo-secret-value-123456", result["readme"]["excerpt"])
        self.assertIn("[REDACTED]", result["readme"]["excerpt"])
        self.assertEqual(result["analyzed_source_files"], ["main.py", "tests/test_main.py"])
        self.assertEqual(result["review"]["task_verification"], "needs_review")
        self.assertEqual(self.client.get("/api/github/analyses").json()[0]["id"], result["id"])
        self.assertEqual(self.client.get(f"/api/github/analyses/{result['id']}").json()["commit_sha"], result["commit_sha"])

        self.client.post("/api/auth/logout")
        self.signup("other@example.com")
        self.assertEqual(self.client.get(f"/api/github/analyses/{result['id']}").status_code, 404)
        self.assertEqual(self.client.get("/api/github/analyses").json(), [])

    def test_github_analysis_rejects_non_repository_urls_before_api_access(self):
        self.signup()
        with patch("backend.main._github_get") as github_get:
            response = self.client.post("/api/github/analyses", json={"repo_url": "https://example.com/owner/repo"})
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
            answer = question["options"][0]["id"] if question["type"] == "objective" else "빈 목록인지 확인하고 예외 처리를 합니다."
            saved = self.client.patch(
                f"/api/assessments/{session['id']}/answers",
                json={"question_id": question["id"], "answer": answer},
            )
            self.assertEqual(saved.status_code, 200)
        self.assertTrue(self.client.post("/api/assessments/start").json()["resumed"])
        with patch("backend.main._grade_written_with_openai", return_value=(7, ["AI 루브릭 평가"])) as grader:
            result = self.client.post(f"/api/assessments/{session['id']}/submit")
        self.assertEqual(grader.call_count, 2)
        self.assertEqual(result.status_code, 200)
        self.assertGreater(result.json()["total_score"], 0)
        self.assertEqual(result.json()["skill_scores"]["코드 이해·오류 분석"], 70)
        self.assertEqual(self.client.post(f"/api/assessments/{session['id']}/submit").json()["total_score"], result.json()["total_score"])
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
        self.assertTrue(all(sum(task["estimated_hours"] for task in week["tasks"]) <= 8 for week in plan_data["weeks"]))
        self.assertTrue(self.client.post(f"/api/plans/{plan_data['id']}/validate").json()["valid"])
        self.assertEqual(self.client.get("/api/plans/current").json()["status"], "draft")
        approved = self.client.post(f"/api/plans/{plan_data['id']}/approve")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(self.client.get("/api/plans/current").json()["status"], "approved")

        progress = self.client.get("/api/progress/dashboard")
        self.assertEqual(progress.status_code, 200, progress.text)
        self.assertEqual(progress.json()["total_tasks"], 8)
        self.assertEqual(progress.json()["completion_rate"], 0)
        task_id = "w1-t1"
        started = self.client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "in_progress", "learning_notes": "API 요청을 구현했습니다."},
        )
        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["status"], "in_progress")
        self.assertTrue(started.json()["learning_start_date"])
        time_log = self.client.post(
            f"/api/tasks/{task_id}/time-logs",
            json={"learning_date": "2026-10-24", "duration_minutes": 60, "notes": "요청 처리 실습"},
        )
        self.assertEqual(time_log.status_code, 201, time_log.text)
        time_edit = self.client.patch(
            f"/api/tasks/{task_id}/time-logs/{time_log.json()['id']}",
            json={"learning_date": "2026-10-24", "duration_minutes": 75, "notes": "오류 처리까지 실습"},
        )
        self.assertEqual(time_edit.status_code, 200, time_edit.text)
        self.assertEqual(time_edit.json()["duration_minutes"], 75)
        submission = self.client.post(
            f"/api/tasks/{task_id}/submissions",
            json={"github_url": "https://github.com/learner/project", "explanation": "기능 구현 결과"},
        )
        self.assertEqual(submission.status_code, 201, submission.text)
        self.assertEqual(self.client.post(
            f"/api/tasks/{task_id}/completion-request",
            json={"completion_criteria_confirmed": False},
        ).status_code, 422)
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
        self.assertEqual(len(self.client.get(f"/api/tasks/{task_id}/time-logs").json()), 1)
        statistics = self.client.get("/api/progress/statistics")
        self.assertEqual(statistics.status_code, 200, statistics.text)
        self.assertEqual(statistics.json()["completion_rate"], 12)
        activities = self.client.get("/api/progress/activities")
        self.assertEqual(activities.status_code, 200, activities.text)
        self.assertEqual(activities.json()[0]["event_type"], "task_completed")
        self.assertIn("time_log_updated", [activity["event_type"] for activity in activities.json()])
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
                    json={"question_id": question["id"], "answer": question["options"][0]["id"]},
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
        content = json.dumps({
            "root_cause_score": 4,
            "root_cause_evidence": "빈 목록에서 첫 항목을 요청하면 인덱스 오류가 발생합니다.",
            "solution_score": 3,
            "solution_evidence": "빈 목록 여부를 먼저 확인하라고 제안했습니다.",
            "clarity_score": 1,
            "clarity_evidence": "설명은 간결하지만 예외 처리 설명은 없습니다.",
            "feedback": "입력 검증을 추가하고 예외 처리 결과도 명시해 보세요.",
        })
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
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }],
                },
            )

        with httpx.Client(transport=httpx.MockTransport(handle_request)) as http_client:
            client = OpenAI(api_key="test-key", http_client=http_client)
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch("backend.main.OpenAI", return_value=client):
                score, feedback = _grade_written_with_openai(QUESTIONS[21], "빈 목록인지 확인하고 예외를 처리합니다.")
        self.assertEqual(score, 8)
        self.assertEqual(len(feedback), 4)
        self.assertEqual(requests[0]["model"], "gpt-4o-mini")
        self.assertEqual(requests[0]["response_format"]["json_schema"]["strict"], True)
        self.assertIn("빈 목록인지 확인하고 예외를 처리합니다.", requests[0]["messages"][1]["content"])

    def test_missing_openai_key_preserves_answers_and_allows_retry(self):
        self.signup()
        self.profile()
        session = self.client.post("/api/assessments/start").json()
        saved = self.client.patch(
            f"/api/assessments/{session['id']}/answers",
            json={"question_id": "q21", "answer": "네트워크 오류와 응답 상태를 확인합니다."},
        )
        self.assertEqual(saved.status_code, 200)
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            failed = self.client.post(f"/api/assessments/{session['id']}/submit")
        self.assertEqual(failed.status_code, 503)
        self.assertIn("OPENAI_API_KEY", failed.json()["detail"])
        resumed = self.client.get(f"/api/assessments/{session['id']}")
        self.assertEqual(resumed.json()["status"], "in_progress")
        self.assertEqual(resumed.json()["answers"]["q21"], "네트워크 오류와 응답 상태를 확인합니다.")


if __name__ == "__main__":
    unittest.main()
