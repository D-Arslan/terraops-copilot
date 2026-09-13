# RAG corpus

Snapshot of TerraOps' public documentation, taken 2026-09-13 from `D:\TerraOps` at commit
`3303dc6`. Copied, not linked: the corpus is versioned with the agent so retrieval is
reproducible. Only files tracked in the TerraOps repository are copied.

| File | Source | Language | Content |
|---|---|---|---|
| `terraops/README.md` | `README.md` | EN | problem, measured findings, architecture, decisions, limits |
| `terraops/DESIGN.md` | `docs/DESIGN.md` | EN | design decisions and caveats: gate, anchors, drift, blur blind spot |
| `terraops/learning.md` | `docs/learning.md` | FR | learning log: DVC, MLflow gate, serving, drift/CT concepts |
| `terraops/params.yaml` | `params.yaml` | EN | promotion thresholds, monitor/trigger parameters (commented) |
| `terraops/prometheus_rules.yml` | `monitoring/rules.yml` | EN | alerting rules and why each threshold |
| `terraops/drift_report_notes.md` | docstring of `src/drift_report.py` | EN | why Wasserstein, capped window, what a report can't say |

What is deliberately NOT here: anything that changes at runtime (served version,
metrics, drift verdicts, log counters). Those come from tools, never from the corpus.
Refresh: re-copy the files, update this table, then `python -m terraops_copilot.rag.ingest`,
`python -m pytest` and `python evaluate.py --agent oracle` (the oracle cites real passages,
so it fails if a documentation case no longer has its passage).
