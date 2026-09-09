# RAG corpus

Snapshot of TerraOps documentation, taken 2026-09-09 from `D:\TerraOps` at commit `7fda55f`.
Copied, not linked: the corpus is versioned with the agent so retrieval is reproducible.

| File | Source | Language | Content |
|---|---|---|---|
| `terraops/README.md` | `README.md` | EN | architecture, measured findings, limits, decisions |
| `terraops/learning.md` | `learning.md` | FR | learning journal: DVC, MLflow gate, serving, drift/CT concepts |
| `terraops/CLAUDE.md` | `CLAUDE.md` | FR | project invariants, commands, known debt |
| `terraops/params.yaml` | `params.yaml` | EN | promotion thresholds, monitor/trigger parameters (commented) |
| `terraops/prometheus_rules.yml` | `monitoring/rules.yml` | EN | alerting rules and why each threshold |
| `terraops/drift_report_notes.md` | docstring of `src/drift_report.py` | EN | why Wasserstein, capped window, what a report can't say |

What is deliberately NOT here: anything that changes at runtime (served version,
metrics, drift verdicts, log counters). Those come from tools, never from the corpus.
Refresh: re-copy the files, then `python -m terraops_copilot.rag.ingest --rebuild`.
