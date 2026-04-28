"""Tests for the FastAPI REST API using a mock agent."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_agent(analytics):
    from observability.tracker import QueryTrace

    agent = MagicMock()
    agent.analytics = analytics
    agent.ask.return_value = {
        "answer": "O produto mais vendido foi Chair B.",
        "conversation_id": "test-conv-123",
        "trace": QueryTrace(
            question="test",
            answer="O produto mais vendido foi Chair B.",
            model="gpt-4o-mini",
            total_duration_ms=500.0,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        ),
    }
    return agent


@pytest.fixture
def client(mock_agent, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with patch("api.routes._get_agent", return_value=mock_agent):
        from api.app import create_app

        app = create_app()
        yield TestClient(app)


class TestHealthCheck:
    def test_health_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestChatEndpoint:
    def test_chat_returns_answer(self, client: TestClient):
        response = client.post(
            "/api/v1/chat",
            json={"question": "Qual produto mais vendido?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Chair B" in data["answer"]
        assert data["conversation_id"] == "test-conv-123"

    def test_chat_includes_metadata(self, client: TestClient):
        response = client.post(
            "/api/v1/chat",
            json={"question": "Qual produto mais vendido?"},
        )
        data = response.json()
        assert "metadata" in data
        assert "tokens" in data["metadata"]

    def test_chat_empty_question_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/chat",
            json={"question": ""},
        )
        assert response.status_code == 422

    def test_chat_with_conversation_id(self, client: TestClient):
        response = client.post(
            "/api/v1/chat",
            json={"question": "E o segundo?", "conversation_id": "existing-123"},
        )
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    def test_overview(self, client: TestClient):
        response = client.get("/api/v1/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_kind"] == "retail"
        assert "unique_orders" in data

    def test_top_products_default(self, client: TestClient):
        response = client.get("/api/v1/analytics/top-products")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"][0]["product_name"] == "Chair B"

    def test_top_products_by_revenue(self, client: TestClient):
        response = client.get("/api/v1/analytics/top-products?by=revenue&n=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

    def test_top_locations(self, client: TestClient):
        response = client.get("/api/v1/analytics/top-locations")
        assert response.status_code == 200
        assert "data" in response.json()

    def test_promotions_unavailable(self, client: TestClient):
        response = client.get("/api/v1/analytics/promotions")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    def test_planned_vs_actual_unavailable(self, client: TestClient):
        response = client.get("/api/v1/analytics/planned-vs-actual")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    def test_service_level_unavailable(self, client: TestClient):
        response = client.get("/api/v1/analytics/service-level")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
