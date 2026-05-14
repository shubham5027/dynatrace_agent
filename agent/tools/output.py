from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from slack_sdk.webhook import WebhookClient


SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK_URL"]
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]


def send_slack_update(incident_id: str, summary: dict[str, Any]) -> dict[str, Any]:
    """
    summary keys:
    - what
    - since
    - action
    - confidence
    - rca_hypothesis
    """
    client = WebhookClient(SLACK_WEBHOOK)
    response = client.send(
        blocks=[
            {"type": "header", "text": {"type": "plain_text", "text": f"Incident: {incident_id}"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*What:*\n{summary.get('what', 'n/a')}"},
                    {"type": "mrkdwn", "text": f"*Since:*\n{summary.get('since', 'n/a')}"},
                ],
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action:* {summary.get('action', 'n/a')}"}},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Root Cause Hypothesis:* {summary.get('rca_hypothesis', 'n/a')}\n"
                        f"*Confidence:* {summary.get('confidence', 'n/a')}%"
                    ),
                },
            },
        ]
    )
    return {"status": response.status_code, "body": response.body}


def create_postmortem_doc(incident_id: str, postmortem_content: str) -> dict[str, Any]:
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_JSON,
        scopes=["https://www.googleapis.com/auth/documents"],
    )
    service = build("docs", "v1", credentials=creds)

    doc = service.documents().create(
        body={"title": f"Postmortem - {incident_id} - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"}
    ).execute()
    doc_id = doc["documentId"]

    service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": postmortem_content,
                    }
                }
            ]
        },
    ).execute()

    return {
        "doc_id": doc_id,
        "url": f"https://docs.google.com/document/d/{doc_id}/edit",
    }
