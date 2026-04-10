import json
import pytest
from unittest.mock import patch, MagicMock
import os
os.environ.setdefault("DB_HOST",     "localhost")
os.environ.setdefault("DB_PORT",     "5432")
os.environ.setdefault("DB_NAME",     "testdb")
os.environ.setdefault("DB_USER",     "test")
os.environ.setdefault("DB_PASSWORD", "test")
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_health_ok(client):
    with patch("app.get_db") as mock_db:
        mock_db.return_value = MagicMock()
        res = client.get("/health")
        assert res.status_code == 200

def test_health_db_fail(client):
    with patch("app.get_db", side_effect=Exception("connection refused")):
        res = client.get("/health")
        assert res.status_code == 500

def test_get_employees_empty(client):
    mock_conn = MagicMock()
    mock_cur  = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchall.return_value = []
    with patch("app.get_db", return_value=mock_conn):
        res = client.get("/api/employees")
        assert res.status_code == 200
        assert json.loads(res.data) == []

def test_add_employee_missing_fields(client):
    res = client.post("/api/employees",
        data=json.dumps({"name": "Harish"}),
        content_type="application/json"
    )
    assert res.status_code == 400

def test_delete_employee_not_found(client):
    mock_conn = MagicMock()
    mock_cur  = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.return_value = None
    with patch("app.get_db", return_value=mock_conn):
        res = client.delete("/api/employees/999")
        assert res.status_code == 404