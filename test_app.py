import json
import os
import tempfile
import unittest

from app import create_app
from app.db import init_db_schema


class TaskManagerApiTestCase(unittest.TestCase):
    def setUp(self):
        db_fd, db_path = tempfile.mkstemp()
        self.db_fd = db_fd
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": db_path,
                "SECRET_KEY": "test-secret",
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db_schema()

    def tearDown(self):
        os.close(self.db_fd)

    # ---- helpers ----
    def _register_and_login(self, email="user@example.com", password="password123"):
        self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": email, "password": password}),
            content_type="application/json",
        )
        resp = self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": email, "password": password}),
            content_type="application/json",
        )
        return resp.get_json()["token"]

    def _auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    # ---- health ----
    def test_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "ok")

    # ---- auth ----
    def test_register_success(self):
        resp = self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": "new@example.com", "password": "password123"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn("token", resp.get_json())

    def test_register_duplicate_email_fails(self):
        self._register_and_login(email="dupe@example.com")
        resp = self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": "dupe@example.com", "password": "password123"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 409)

    def test_login_wrong_password_fails(self):
        self._register_and_login(email="wrongpass@example.com", password="password123")
        resp = self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "wrongpass@example.com", "password": "nope"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    # ---- tasks ----
    def test_tasks_require_auth(self):
        resp = self.client.get("/api/tasks")
        self.assertEqual(resp.status_code, 401)

    def test_create_and_list_task(self):
        token = self._register_and_login()
        resp = self.client.post(
            "/api/tasks",
            data=json.dumps({"title": "Test task", "status": "pending"}),
            content_type="application/json",
            headers=self._auth_header(token),
        )
        self.assertEqual(resp.status_code, 201)

        resp = self.client.get("/api/tasks", headers=self._auth_header(token))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()), 1)

    def test_create_task_missing_title_fails(self):
        token = self._register_and_login()
        resp = self.client.post(
            "/api/tasks",
            data=json.dumps({"status": "pending"}),
            content_type="application/json",
            headers=self._auth_header(token),
        )
        self.assertEqual(resp.status_code, 400)

    def test_update_and_delete_task(self):
        token = self._register_and_login()
        create_resp = self.client.post(
            "/api/tasks",
            data=json.dumps({"title": "Original title"}),
            content_type="application/json",
            headers=self._auth_header(token),
        )
        task_id = create_resp.get_json()["id"]

        update_resp = self.client.put(
            f"/api/tasks/{task_id}",
            data=json.dumps({"status": "completed"}),
            content_type="application/json",
            headers=self._auth_header(token),
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.get_json()["status"], "completed")

        delete_resp = self.client.delete(
            f"/api/tasks/{task_id}", headers=self._auth_header(token)
        )
        self.assertEqual(delete_resp.status_code, 200)

        get_resp = self.client.get(
            f"/api/tasks/{task_id}", headers=self._auth_header(token)
        )
        self.assertEqual(get_resp.status_code, 404)

    def test_users_cannot_access_others_tasks(self):
        token_a = self._register_and_login(email="a@example.com")
        token_b = self._register_and_login(email="b@example.com")

        create_resp = self.client.post(
            "/api/tasks",
            data=json.dumps({"title": "User A's task"}),
            content_type="application/json",
            headers=self._auth_header(token_a),
        )
        task_id = create_resp.get_json()["id"]

        resp = self.client.get(
            f"/api/tasks/{task_id}", headers=self._auth_header(token_b)
        )
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
