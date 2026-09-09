"""The drift tool must pass 'inconclusive' through, never turn it into 'no drift'."""
from terraops_copilot.tools.drift import DriftArgs, _compact


def test_inconclusive_is_preserved():
    summary = {"status": "insufficient_data", "n_current": 6, "min_current_rows": 200,
               "dataset_drift": False, "message": "only 6 rows in the window; 200 required",
               "window": {"newest_ts": "2026-09-09"}}
    out = _compact(summary, DriftArgs(since_days=7))
    assert out["verdict"] == "inconclusive" and out["n_rows_in_window"] == 6
    assert "no_drift" not in out.values()


def test_drift_verdict_is_compacted():
    summary = {"status": "ok", "n_current": 260, "min_current_rows": 200,
               "dataset_drift": True, "drifted_count": 11, "drifted_share": 0.9167,
               "drift_share_threshold": 0.5, "stattest": "wasserstein",
               "features": {f"f{i}": {} for i in range(12)},
               "top_drifted": [{"feature": "mean_b", "distance": 1.4449, "drifted": True}] * 5,
               "predictions": {"predicted_class_share": {"SeaLake": 0.63}},
               "window": {"newest_ts": "x"}}
    out = _compact(summary, DriftArgs(since_days=1))
    assert out["verdict"] == "drift" and out["drifted_features"] == "11/12"
    assert len(out["top_drifted"]) == 3 and out["drifted_share"] == 0.92
