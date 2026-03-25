import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from fahr_ai.api import health

app = FastAPI()
app.include_router(health.router, prefix="/api/v1")
client = TestClient(app)


def test_health_ok(monkeypatch):
    monkeypatch.setattr(health, "check_llm", lambda: True)
    monkeypatch.setattr(health, "check_database", lambda: True)
    monkeypatch.setattr(health, "check_tts_stt", lambda: True)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_critical_down(monkeypatch):
    monkeypatch.setattr(health, "check_llm", lambda: False)
    monkeypatch.setattr(health, "check_database", lambda: False)
    monkeypatch.setattr(health, "check_tts_stt", lambda: True)

    response = client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
    assert response.json()["services"]["llm"] == "down"
    assert response.json()["services"]["database"] == "down"


def test_health_noncritical_down(monkeypatch):
    monkeypatch.setattr(health, "check_llm", lambda: True)
    monkeypatch.setattr(health, "check_database", lambda: True)
    monkeypatch.setattr(health, "check_tts_stt", lambda: False)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["services"]["tts_stt"] == "down"
