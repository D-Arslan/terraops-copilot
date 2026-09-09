"""Thin HTTP client for TerraOps (API :8000) and its MLflow registry (:5000).

Known behaviour (Sprint 0): after `docker compose up`, port 8000 is published ~40 s
before uvicorn listens. During that window the connection is accepted then dropped
(`RemoteDisconnected`), which requests reports as ConnectionError - not a refusal.
`wait_ready` exists for that window.
"""
from __future__ import annotations

import os
import time

import requests

SOURCE_HEADER = {"X-TerraOps-Source": "agent:copilot"}  # never mix agent traffic with real


class TerraOpsClient:
    def __init__(self, api_url: str | None = None, mlflow_url: str | None = None,
                 timeout: float = 15.0):
        self.api_url = (api_url or os.getenv("TERRAOPS_API_URL", "http://localhost:8000")).rstrip("/")
        self.mlflow_url = (mlflow_url or os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")).rstrip("/")
        self.timeout = timeout
        self._s = requests.Session()
        self._s.headers.update(SOURCE_HEADER)

    # -- serving API ----------------------------------------------------------
    def health(self) -> dict:
        r = self._s.get(f"{self.api_url}/health", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def model_info(self) -> dict:
        r = self._s.get(f"{self.api_url}/model-info", timeout=self.timeout)
        r.raise_for_status()  # 503 while the API boots without a model
        return r.json()

    def monitoring_status(self) -> dict:
        r = self._s.get(f"{self.api_url}/monitoring/status", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def wait_ready(self, seconds: float = 90.0) -> dict:
        deadline = time.time() + seconds
        last_exc: Exception | None = None
        while time.time() < deadline:
            try:
                return self.health()
            except requests.ConnectionError as exc:
                last_exc = exc
                time.sleep(2)
        raise TimeoutError(f"TerraOps API not ready after {seconds}s: {last_exc}")

    # -- MLflow registry ------------------------------------------------------
    def registry_model_by_alias(self, name: str, alias: str) -> dict:
        """GET /api/2.0/mlflow/registered-models/alias -> the model version + tags.

        Returns the registry's view (what *should* be served), which can differ from
        /model-info (what *is* served) until someone calls POST /reload.
        """
        r = self._s.get(f"{self.mlflow_url}/api/2.0/mlflow/registered-models/alias",
                        params={"name": name, "alias": alias}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()["model_version"]
