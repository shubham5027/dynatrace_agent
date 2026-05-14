"""
Cloud Run endpoint that receives Dynatrace problem webhooks
and triggers a Vertex AI Agent Builder session.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request
import google.auth
import google.auth.transport.requests
import requests as http_requests


app = Flask(__name__)

AGENT_ID = os.environ.get("AGENT_BUILDER_ID", "temp-agent-id")
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")


def get_bearer_token() -> str:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return creds.token


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True}), 200


@app.route("/webhook/dynatrace", methods=["POST"])
def receive_dynatrace_alert():
    payload = request.get_json(silent=True) or {}
    problem_id = payload.get("ProblemID")
    problem_title = payload.get("ProblemTitle")
    impact = payload.get("ImpactedEntity")

    if not problem_id:
        return jsonify({"error": "Missing ProblemID"}), 400

    agent_url = (
        f"https://{LOCATION}-dialogflow.googleapis.com/v3/"
        f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/sessions/-:detectIntent"
    )
    trigger_message = (
        f"New incident detected. Problem ID: {problem_id}. "
        f"Title: {problem_title}. Impacted: {impact}. "
        "Begin incident response workflow."
    )

    response = http_requests.post(
        agent_url,
        headers={"Authorization": f"Bearer {get_bearer_token()}"},
        json={
            "queryInput": {
                "text": {"text": trigger_message},
                "languageCode": "en",
            }
        },
        timeout=30,
    )

    return jsonify({"triggered": response.ok, "status_code": response.status_code, "response": response.json()}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
