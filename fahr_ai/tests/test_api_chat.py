import pytest
from fastapi.testclient import TestClient
from fahr_ai.api.chat import router, sessions_db
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)


def test_missing_prompt():
    response = client.post("/api/v1/chat", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "Prompt is required"


def test_create_chat_and_session():
    response = client.post("/api/v1/chat", json={"prompt": "Hello"})
    assert response.status_code == 200
    assert "data: " in response.text
    assert len(sessions_db) == 1


def test_reuse_session():
    response1 = client.post("/api/v1/chat", json={"prompt": "Start chat"})
    session_id = list(sessions_db.keys())[0]

    response2 = client.post("/api/v1/chat", json={"prompt": "Follow-up", "session_id": session_id})
    assert response2.status_code == 200
    assert session_id in response2.headers["x-session-id"].lower()


def test_invalid_session():
    response = client.post("/api/v1/chat", json={"prompt": "Hi", "session_id": "fake_id"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_get_session_success():
    response = client.post("/api/v1/chat", json={"prompt": "Hello"})
    session_id = list(sessions_db.keys())[0]

    get_response = client.get(f"/api/v1/session/{session_id}")
    assert get_response.status_code == 200
    assert get_response.json()["messages"][0]["content"] == "Hello"


def test_get_session_failure():
    response = client.get("/api/v1/session/invalid123")
    assert response.status_code == 404
