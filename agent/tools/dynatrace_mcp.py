"""
Dynatrace MCP-style tool wrappers.

These are plain HTTP wrappers for Dynatrace APIs that can be registered as tools
in an agent orchestrator.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests


DT_URL = os.environ["DYNATRACE_URL"].rstrip("/")
DT_TOKEN = os.environ["DYNATRACE_API_TOKEN"]

HEADERS = {
    "Authorization": f"Api-Token {DT_TOKEN}",
    "Content-Type": "application/json",
}


def get_active_problems(impact_level: str | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {"status": "OPEN", "pageSize": 10}
    if impact_level:
        params["impactLevel"] = impact_level

    resp = requests.get(f"{DT_URL}/api/v2/problems", headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_problem_details(problem_id: str) -> dict[str, Any]:
    resp = requests.get(f"{DT_URL}/api/v2/problems/{problem_id}", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_service_metrics(entity_id: str, metric_key: str, minutes_back: int = 30) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(minutes=minutes_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "metricSelector": f"{metric_key}:filter(eq(dt.entity.service,{entity_id}))",
        "from": start,
        "to": end,
        "resolution": "1m",
    }
    resp = requests.get(f"{DT_URL}/api/v2/metrics/query", headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_distributed_traces(service_name: str, minutes_back: int = 15) -> dict[str, Any]:
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = now - (minutes_back * 60 * 1000)

    payload = {
        "query": f'service.name="{service_name}" AND status=ERROR',
        "startTimestamp": start,
        "endTimestamp": now,
        "limit": 20,
    }
    resp = requests.post(f"{DT_URL}/api/v2/traces", headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_logs(entity_id: str, minutes_back: int = 15, log_level: str = "ERROR") -> dict[str, Any]:
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = now - (minutes_back * 60 * 1000)

    params = {
        "query": f'dt.entity.service="{entity_id}" AND level="{log_level}"',
        "from": start,
        "to": now,
        "limit": 50,
    }
    resp = requests.get(f"{DT_URL}/api/v2/logs/search", headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_deployment_events(entity_id: str, minutes_back: int = 60) -> dict[str, Any]:
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = now - (minutes_back * 60 * 1000)

    params = {
        "entitySelector": f'entityId("{entity_id}")',
        "eventType": "CUSTOM_DEPLOYMENT",
        "from": start,
        "to": now,
    }
    resp = requests.get(f"{DT_URL}/api/v2/events", headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()
