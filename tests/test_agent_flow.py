import os

os.environ.setdefault("AGENT_BUILDER_ID", "dummy-agent")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "dummy-project")

from agent.webhook_trigger import app  # noqa: E402
import agent.webhook_trigger as webhook  # noqa: E402


def test_healthz():
    client = app.test_client()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json["ok"] is True


def test_webhook_missing_problem_id():
    client = app.test_client()
    response = client.post("/webhook/dynatrace", json={})
    assert response.status_code == 400
    assert response.json["error"] == "Missing ProblemID"


def test_webhook_success(monkeypatch):
    class FakeResponse:
        ok = True
        status_code = 200

        @staticmethod
        def json():
            return {"result": "triggered"}

    def fake_post(url, headers, json, timeout):
        assert "dialogflow.googleapis.com" in url
        assert headers["Authorization"] == "Bearer fake-token"
        assert "queryInput" in json
        assert timeout == 30
        return FakeResponse()

    monkeypatch.setattr(webhook, "get_bearer_token", lambda: "fake-token")
    monkeypatch.setattr(webhook.http_requests, "post", fake_post)

    client = app.test_client()
    response = client.post(
        "/webhook/dynatrace",
        json={
            "ProblemID": "P-TEST-001",
            "ProblemTitle": "Payment errors",
            "ImpactedEntity": "payment-service",
        },
    )

    assert response.status_code == 200
    assert response.json["triggered"] is True
    assert response.json["status_code"] == 200
