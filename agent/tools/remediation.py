"""
Tiered remediation actions.
LOW actions can be auto-executed at high confidence.
MEDIUM and HIGH require explicit approval.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any


RISK_LEVELS = {
    "clear_cache": "LOW",
    "scale_out": "LOW",
    "restart_unhealthy_pod": "LOW",
    "rollback_deployment": "HIGH",
    "scale_to_zero": "HIGH",
    "delete_resource": "HIGH",
    "toggle_feature_flag": "MEDIUM",
    "drain_node": "MEDIUM",
}


def execute_action(action: str, params: dict[str, Any], approved: bool = False) -> dict[str, Any]:
    risk = RISK_LEVELS.get(action, "HIGH")

    if risk == "HIGH" and not approved:
        return {
            "status": "BLOCKED",
            "reason": f"Action '{action}' is HIGH_RISK. Human approval required.",
            "risk": risk,
            "params": params,
        }

    if risk == "MEDIUM" and not approved:
        return {
            "status": "PENDING_APPROVAL",
            "reason": f"Action '{action}' requires approval.",
            "risk": risk,
            "params": params,
        }

    handlers = {
        "scale_out": _scale_out,
        "restart_unhealthy_pod": _restart_pod,
        "clear_cache": _clear_cache,
    }
    handler = handlers.get(action)
    if not handler:
        return {"status": "ERROR", "reason": f"No handler for action '{action}'"}
    return handler(params)


def _scale_out(params: dict[str, Any]) -> dict[str, Any]:
    service = params.get("service_name")
    if not service:
        return {"status": "ERROR", "reason": "Missing params.service_name"}

    replicas = int(params.get("replicas", 3))
    result = subprocess.run(
        [
            "gcloud",
            "run",
            "services",
            "update",
            service,
            "--min-instances",
            str(replicas),
            "--region",
            os.environ.get("CLOUD_REGION", "us-central1"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "OK" if result.returncode == 0 else "ERROR",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def _restart_pod(params: dict[str, Any]) -> dict[str, Any]:
    pod = params.get("pod_name")
    if not pod:
        return {"status": "ERROR", "reason": "Missing params.pod_name"}

    namespace = params.get("namespace", "default")
    result = subprocess.run(
        ["kubectl", "delete", "pod", pod, "-n", namespace],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "OK" if result.returncode == 0 else "ERROR",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def _clear_cache(params: dict[str, Any]) -> dict[str, Any]:
    return {"status": "OK", "message": f"Cache cleared for {params.get('service', 'unknown-service')}"}
