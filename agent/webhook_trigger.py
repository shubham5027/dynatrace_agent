"""
Cloud Run endpoint that receives Dynatrace problem webhooks
and exposes Dynatrace tool APIs for Vertex AI Agent Builder.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request
import google.auth
import google.auth.transport.requests
import requests as http_requests

from agent.tools.dynatrace_mcp import (
    get_active_problems,
    get_problem_details,
    get_service_metrics,
    get_distributed_traces,
    get_logs,
    get_deployment_events,
)

app = Flask(__name__)

# Environment variables
AGENT_ID = os.environ.get("AGENT_BUILDER_ID", "temp-agent-id")
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")


# -----------------------------------
# Google Auth Token
# -----------------------------------
def get_bearer_token() -> str:
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return creds.token


# -----------------------------------
# Health Check
# -----------------------------------
@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "healthy"}), 200


# -----------------------------------
# Dynatrace Tool APIs
# -----------------------------------
@app.route("/get_active_problems", methods=["GET"])
def active_problems():
    try:
        result = get_active_problems()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_problem_details", methods=["POST"])
def problem_details():
    try:
        data = request.get_json(silent=True) or {}
        problem_id = data.get("problem_id")

        if not problem_id:
            return jsonify({"error": "Missing problem_id"}), 400

        result = get_problem_details(problem_id)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_service_metrics", methods=["POST"])
def service_metrics():
    try:
        data = request.get_json(silent=True) or {}

        entity_id = data.get("entity_id")
        metric_key = data.get("metric_key")

        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400

        if not metric_key:
            return jsonify({"error": "Missing metric_key"}), 400

        result = get_service_metrics(entity_id, metric_key)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_distributed_traces", methods=["POST"])
def distributed_traces():
    try:
        data = request.get_json(silent=True) or {}

        service_name = data.get("service_name")

        if not service_name:
            return jsonify({"error": "Missing service_name"}), 400

        result = get_distributed_traces(service_name)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_logs", methods=["POST"])
def logs():
    try:
        data = request.get_json(silent=True) or {}

        entity_id = data.get("entity_id")

        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400

        result = get_logs(entity_id)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_deployment_events", methods=["POST"])
def deployment_events():
    try:
        data = request.get_json(silent=True) or {}

        entity_id = data.get("entity_id")

        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400

        result = get_deployment_events(entity_id)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------
# Dynatrace Webhook → Agent Builder
# -----------------------------------
@app.route("/webhook/dynatrace", methods=["POST"])
def receive_dynatrace_alert():
    try:
        payload = request.get_json(silent=True) or {}

        problem_id = payload.get("ProblemID")
        problem_title = payload.get("ProblemTitle")
        impact = payload.get("ImpactedEntity")

        if not problem_id:
            return jsonify({"error": "Missing ProblemID"}), 400

        agent_url = (
            f"https://{LOCATION}-dialogflow.googleapis.com/v3/"
            f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/"
            f"{AGENT_ID}/sessions/-:detectIntent"
        )

        trigger_message = (
            f"New incident detected. "
            f"Problem ID: {problem_id}. "
            f"Title: {problem_title}. "
            f"Impacted: {impact}. "
            f"Begin incident response workflow."
        )

        response = http_requests.post(
            agent_url,
            headers={
                "Authorization": f"Bearer {get_bearer_token()}"
            },
            json={
                "queryInput": {
                    "text": {
                        "text": trigger_message
                    },
                    "languageCode": "en"
                }
            },
            timeout=30,
        )

        return jsonify({
            "triggered": response.ok,
            "status_code": response.status_code,
            "response": response.json()
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------
# Local Run
# -----------------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080"))
    )