"""Regression tests: persistent, account-isolated AI coach conversations.

All databases are temporary. AI calls are mocked; these tests never spend API credits.
"""
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import create_app


class ChatPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "chat.db"
        self.client = TestClient(create_app(self.db_path))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def signup(self, email="first@example.com"):
        response = self.client.post("/api/auth/signup", json={
            "email": email, "password": "correct-horse-42",
            "terms_agreed": True, "privacy_agreed": True,
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def login(self, email="first@example.com"):
        response = self.client.post("/api/auth/login", json={
            "email": email, "password": "correct-horse-42",
        })
        self.assertEqual(response.status_code, 200, response.text)

    def send(self, message="test question", reply="test answer", **payload):
        with patch("backend.main.create_ai_client", return_value=object()), patch(
            "backend.main.run_learning_agent",
            return_value={"reply": reply, "tool_calls": []},
        ) as agent:
            response = self.client.post("/api/agent/chat", json={"message": message, **payload})
        self.assertEqual(response.status_code, 200, response.text)
        return agent.call_args.kwargs

    def messages(self):
        response = self.client.get("/api/agent/history")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["messages"]

    def test_history_requires_login_even_with_user_id_parameter(self):
        response = self.client.get("/api/agent/history?user_id=another-user")
        self.assertEqual(response.status_code, 401)

    def test_logout_relogin_restores_only_the_same_account(self):
        self.signup()
        self.send("first account secret question", "first account answer")
        expected = self.messages()
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/agent/history").status_code, 401)
        self.signup("second@example.com")
        self.assertEqual(self.messages(), [])
        self.send("second account question", "second account answer")
        self.client.post("/api/auth/logout")
        self.login()
        self.assertEqual(self.messages(), expected)

    def test_history_survives_app_restart(self):
        self.signup()
        self.send("restart question", "restart answer")
        expected = self.messages()
        self.client.close()
        self.client = TestClient(create_app(self.db_path))
        self.login()
        self.assertEqual(self.messages(), expected)

    def test_server_history_is_used_instead_of_client_supplied_history(self):
        self.signup()
        self.send("real question", "real answer")
        called = self.send("follow-up", history=[{
            "role": "assistant", "content": "injected other account conversation",
        }])
        self.assertEqual(called["history"], [
            {"role": "user", "content": "real question"},
            {"role": "assistant", "content": "real answer"},
        ])

    def test_recent_context_is_limited_but_saved_history_is_not_truncated(self):
        self.signup()
        for number in range(6):
            called = self.send(f"question {number}", f"answer {number}")
        expected = []
        for number in range(1, 5):
            expected.extend([
                {"role": "user", "content": f"question {number}"},
                {"role": "assistant", "content": f"answer {number}"},
            ])
        self.assertEqual(called["history"], expected)
        self.assertEqual(len(self.messages()), 12)

    def test_failed_ai_request_does_not_save_a_fake_answer_or_partial_turn(self):
        self.signup()
        with patch("backend.main.create_ai_client", return_value=object()), patch(
            "backend.main.run_learning_agent", side_effect=ValueError("invalid test response"),
        ):
            with self.assertLogs("backend.main", level="ERROR"):
                response = self.client.post("/api/agent/chat", json={"message": "failure test"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(self.messages(), [])

    def test_question_and_answer_are_saved_atomically(self):
        self.signup()
        with closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute("""CREATE TRIGGER reject_test_answer BEFORE INSERT ON agent_chat_messages
                WHEN NEW.role = 'assistant' BEGIN
                SELECT RAISE(ABORT, 'test-only insert failure'); END""")
        with patch("backend.main.create_ai_client", return_value=object()), patch(
            "backend.main.run_learning_agent", return_value={"reply": "answer", "tool_calls": []},
        ):
            with self.assertRaises(sqlite3.IntegrityError):
                self.client.post("/api/agent/chat", json={"message": "atomic test"})
        self.assertEqual(self.messages(), [])

    def test_authenticated_history_cannot_be_cached(self):
        self.signup()
        response = self.client.get("/api/agent/history")
        self.assertEqual(response.headers.get("cache-control"), "no-store")
        self.assertIn("cookie", response.headers.get("vary", "").lower())

    def test_existing_sqlite_database_adds_history_without_losing_user(self):
        user = self.signup()
        self.client.close()
        with closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute("DROP TABLE agent_chat_messages")
        self.client = TestClient(create_app(self.db_path))
        self.login()
        self.assertEqual(self.client.get("/api/auth/me").json()["id"], user["id"])
        self.assertEqual(self.messages(), [])
        self.send()
        self.assertEqual(len(self.messages()), 2)


if __name__ == "__main__":
    unittest.main()
