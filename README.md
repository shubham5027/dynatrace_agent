# SRE Copilot

Incident response copilot using Dynatrace telemetry plus Google Cloud Agent Builder.

## Implemented so far
- Dynatrace API wrappers: `agent/tools/dynatrace_mcp.py`
- Remediation engine: `agent/tools/remediation.py`
- Output layer (Slack + Google Docs): `agent/tools/output.py`
- Prompts: `agent/prompts/system_prompt.txt`, `agent/prompts/rca_prompt.txt`
- Cloud Run webhook trigger: `agent/webhook_trigger.py`
- Demo payload: `demo/mock_alert.json`

## Local setup
```bash
python -m venv .venv
. .venv/Scripts/activate  # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Required environment variables
```bash
# Dynatrace
DYNATRACE_URL=https://YOUR_ENV.live.dynatrace.com
DYNATRACE_API_TOKEN=...

# Slack + Google Docs
SLACK_WEBHOOK_URL=...
GOOGLE_SERVICE_ACCOUNT_JSON=/abs/path/service-account.json

# Agent Builder trigger
AGENT_BUILDER_ID=...
GOOGLE_CLOUD_PROJECT=...
GOOGLE_CLOUD_LOCATION=us-central1
```

## Run locally
```bash
python -m agent.webhook_trigger
```

Test webhook:
```bash
curl -X POST http://localhost:8080/webhook/dynatrace ^
  -H "Content-Type: application/json" ^
  -d @demo/mock_alert.json
```

## Run tests
```bash
pytest -q
```

## Deploy
```bash
gcloud run deploy sre-copilot-webhook \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_BUILDER_ID=YOUR_AGENT_ID,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT
```
