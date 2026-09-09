"""Sprint 0 acceptance test: probe the 7 TerraOps endpoints over HTTP.

Read-only from the agent project's point of view: TerraOps code is never touched,
only called. Exit code 0 iff every endpoint answers as expected.

Usage:
    python scripts/audit_terraops.py [--base-url http://localhost:8000]
                                     [--image path/to/tile.jpg]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

DEFAULT_IMAGE = Path(r"D:\TerraOps\data\raw\eurosat\2750\AnnualCrop\AnnualCrop_1.jpg")


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"[{'OK ' if ok else 'KO '}] {name:<28} {detail}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")
    results: list[bool] = []

    # 1. GET /health — always 200, tells us whether the model is loaded.
    r = requests.get(f"{base}/health", timeout=10)
    body = r.json()
    results.append(check("GET /health", r.status_code == 200,
                         f"model_loaded={body.get('model_loaded')} version={body.get('model_version')}"))

    # 2. GET /model-info — 503 while degraded, 200 with class list otherwise.
    r = requests.get(f"{base}/model-info", timeout=10)
    body = r.json()
    results.append(check("GET /model-info", r.status_code == 200,
                         f"{body.get('registry_model')}@{body.get('alias')} v{body.get('model_version')} "
                         f"classes={body.get('num_classes')} device={body.get('device')}"))

    # 3. POST /predict — multipart, one file, optional X-TerraOps-Source header.
    with args.image.open("rb") as fh:
        r = requests.post(f"{base}/predict", files={"file": (args.image.name, fh, "image/jpeg")},
                          headers={"X-TerraOps-Source": "agent:audit"}, timeout=60)
    body = r.json()
    results.append(check("POST /predict", r.status_code == 200,
                         f"{body.get('predicted_class')} conf={body.get('confidence', 0):.3f} "
                         f"(expected {args.image.parent.name})"))

    # 4. POST /predict/batch — multipart, repeated `files` field.
    with args.image.open("rb") as f1, args.image.open("rb") as f2:
        r = requests.post(f"{base}/predict/batch",
                          files=[("files", (args.image.name, f1, "image/jpeg")),
                                 ("files", (args.image.name, f2, "image/jpeg"))],
                          headers={"X-TerraOps-Source": "agent:audit"}, timeout=60)
    body = r.json()
    n = len(body.get("predictions", []))
    results.append(check("POST /predict/batch", r.status_code == 200 and n == 2,
                         f"{n} predictions, model_version={body.get('model_version')}"))

    # 5. GET /metrics — Prometheus text format, NOT JSON.
    r = requests.get(f"{base}/metrics", timeout=10)
    results.append(check("GET /metrics", r.status_code == 200 and "terraops" in r.text,
                         f"{len(r.text.splitlines())} lines, content-type={r.headers.get('content-type','').split(';')[0]}"))

    # 6. GET /monitoring/status — health of the prediction log itself.
    r = requests.get(f"{base}/monitoring/status", timeout=10)
    body = r.json()
    results.append(check("GET /monitoring/status", r.status_code == 200,
                         f"log_ready={body.get('log_ready')} written={body.get('rows_written')} "
                         f"dropped={body.get('rows_dropped')}"))

    # 7. POST /reload — no body; no-op (reloaded=false) if @champion unchanged.
    r = requests.post(f"{base}/reload", timeout=120)
    body = r.json()
    results.append(check("POST /reload", r.status_code == 200,
                         f"reloaded={body.get('reloaded')} version={body.get('version')} "
                         f"previous={body.get('previous_version')}"))

    print(f"\n{sum(results)}/7 endpoints OK")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
