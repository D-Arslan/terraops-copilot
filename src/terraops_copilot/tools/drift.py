"""get_drift_report: live drift verdict over a recent window of the prediction log.

TerraOps has no HTTP endpoint for drift (known debt): the verdict comes from
`src/drift_report.py`, a CLI reading Postgres and Evidently. We run that CLI as a
subprocess in the TerraOps repo - calling it, not modifying it - and read the JSON
summary it writes. Reports go to a scratch dir so the agent never pollutes
`monitoring/reports/`.

The CLI can answer 'insufficient_data' (fewer rows than monitor.min_current_rows).
That is a real, honest answer and the tool passes it through untouched: an agent
that turns 'not enough data' into 'no drift' is worse than no agent.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from pydantic import BaseModel, Field

from .base import Tool

DEFAULT_REPO = Path(os.getenv("TERRAOPS_REPO", r"D:\TerraOps"))
DEFAULT_DB_URI = os.getenv("TERRAOPS_DB_URI", "postgresql://mlflow:mlflow@localhost:55433/mlflow")


class DriftArgs(BaseModel):
    model_config = {"extra": "forbid"}
    since_days: int = Field(default=7, ge=1, le=90,
                            description="Look-back window in days (1-90). 'This week' = 7, "
                                        "'today' = 1, 'this month' = 30.")
    source: str | None = Field(
        default=None,
        description="Optional X-TerraOps-Source filter, e.g. 'ui' for real uploads or "
                    "'sim:cloud:0.6' for simulated traffic. Leave empty for all traffic.")


def run_drift_report(args: DriftArgs, repo: Path = DEFAULT_REPO,
                     db_uri: str = DEFAULT_DB_URI, timeout: float = 180.0) -> dict:
    out_dir = Path(tempfile.gettempdir()) / "terraops-copilot-drift"
    out_dir.mkdir(exist_ok=True)
    stem = f"agent_{int(time.time())}"
    cmd = [sys.executable, str(repo / "src" / "drift_report.py"),
           "--since-minutes", str(args.since_days * 1440),
           "--out-dir", str(out_dir), "--name", stem]
    if args.source:
        cmd += ["--source", args.source]
    env = {**os.environ, "TERRAOPS_DB_URI": db_uri, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True,
                          timeout=timeout, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"drift_report.py failed (rc={proc.returncode}): "
                           f"{proc.stderr.strip()[-600:]}")
    summary = json.loads((out_dir / f"{stem}.json").read_text(encoding="utf-8"))
    return _compact(summary, args)


def _compact(s: dict, args: DriftArgs) -> dict:
    """Only what the model needs to answer - not 12 feature distances."""
    out = {
        "window_days": args.since_days,
        "source_filter": args.source,
        "status": s.get("status"),                     # 'ok' | 'insufficient_data'
        "n_rows_in_window": s.get("n_current"),
        "min_rows_required": s.get("min_current_rows"),
        "newest_row": (s.get("window") or {}).get("newest_ts"),
    }
    if s.get("status") != "ok":
        out["verdict"] = "inconclusive"
        out["message"] = s.get("message")
        return out
    out.update({
        "verdict": "drift" if s.get("dataset_drift") else "no_drift",
        "drifted_features": f"{s.get('drifted_count')}/{len(s.get('features', {}))}",
        "drifted_share": round(s.get("drifted_share", 0.0), 2),
        "drift_share_threshold": s.get("drift_share_threshold"),
        "stattest": s.get("stattest"),
        "top_drifted": [{"feature": t["feature"], "distance": round(t["distance"], 3)}
                        for t in s.get("top_drifted", [])[:3]],
        "predicted_class_share": (s.get("predictions") or {}).get("predicted_class_share"),
    })
    return out


def build_drift_tool() -> Tool:
    return Tool(
        name="get_drift_report",
        description=(
            "Compute the CURRENT data-drift verdict: compares the recent prediction "
            "traffic (last N days, from the prediction log) against the frozen training "
            "reference with Evidently. Use for 'is there drift now / this week / today?', "
            "'are the inputs still like the training data?', 'which features moved?'. "
            "Returns verdict ('drift' | 'no_drift' | 'inconclusive'), rows in the window "
            "vs rows required, drifted feature share and the top drifted features. An "
            "'inconclusive' verdict means too little traffic to decide - report it as "
            "such, never as 'no drift'. Do NOT use it to EXPLAIN what drift is or how it "
            "is detected: that is documentation (search_documentation). Takes a few "
            "seconds."
        ),
        args_model=DriftArgs,
        run=run_drift_report,
    )
