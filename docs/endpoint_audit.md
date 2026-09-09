# TerraOps API audit — Sprint 0 (2026-09-09)

Source of truth: `D:\TerraOps\src\api.py` + live `GET /openapi.json`. Verified with
`python scripts/audit_terraops.py` → **7/7 OK** (champion `terraops-eurosat` v1, CPU).

Startup note: the container publishes port 8000 before uvicorn listens (torch import +
model pull from MLflow, ~40 s). Until then the TCP connection is *accepted then closed*
(`RemoteDisconnected`), not refused. The agent's HTTP client must treat that as
"not ready yet", not as "API down".

## Endpoint contract

| # | Method + path | Input | Output (200) | Errors |
|---|---|---|---|---|
| 1 | `GET /health` | none | `{status:"ok", model_loaded:bool, model_version:str\|null, tracking_uri}` | never (always 200, liveness) |
| 2 | `GET /model-info` | none | `{registry_model, alias:"champion", model_version, num_classes:10, classes:[10 str], image_size, device, loaded_at:epoch, tracking_uri}` | 503 if no model loaded (degraded boot) |
| 3 | `POST /predict` | multipart `file` (image bytes); optional header `X-TerraOps-Source` | `{predicted_class, confidence, probabilities:{class:p ×10}, model_version}` | 422 missing file; 400 undecodable image; 503 degraded |
| 4 | `POST /predict/batch` | multipart repeated `files`; same header | `{predictions:[Prediction…], model_version}` | idem |
| 5 | `GET /metrics` | none | **Prometheus text exposition** (not JSON): request counters, latency histograms, class mix, log gauges | never |
| 6 | `GET /monitoring/status` | none | `{log_ready, rows_written, rows_dropped, flush_failures, queue_depth, last_error}` | never |
| 7 | `POST /reload` | none (no body) | `{reloaded:bool, version, previous_version}` — `reloaded=false` if `@champion` unchanged | 503 registry unreachable / no champion |

Every prediction carries `model_version`: the agent can always say *which* model answered.

Observed error bodies (useful for the tool executors):

```json
// 422 — missing multipart field (FastAPI/Pydantic)
{"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]}
// 400 — bytes are not an image
{"detail":"Cannot decode image: cannot identify image file <_io.BytesIO ...>"}
```

## Endpoint → natural-language intent

| Endpoint | Question a user would ask | Tool nature | Agent-side caveat |
|---|---|---|---|
| `GET /health` | « Est-ce que l'API tourne ? Le modèle est-il chargé ? » | read, safe, cheap | Always 200: the *content* (`model_loaded`) is the signal, not the status code. |
| `GET /model-info` | « Quel modèle est servi en ce moment ? Quelle version ? Quelles classes sait-il reconnaître ? » | read, safe | Answers traceability *now*, not history (« quelle version a répondu hier ? » → MLflow/log, later sprint). |
| `POST /predict` | « Classe cette image / cette tuile : forêt ou culture ? Avec quelle confiance ? » | read-ish (writes to prediction log) | The LLM cannot see pixels: the tool takes a **file path** and does the upload. Tag traffic `X-TerraOps-Source: agent`. |
| `POST /predict/batch` | « Classe toutes les tuiles de ce dossier et donne-moi la répartition par classe. » | idem, bulk | Tool must bound the batch size and **summarise**: never dump 200 probability vectors into the context window. |
| `GET /metrics` | « Combien de requêtes depuis le démarrage ? Quelle latence p95 ? Quelle classe est la plus prédite ? » | read, safe | Raw Prometheus text is hostile to an LLM: the tool must **parse and return a small JSON**. Time-ranged questions (« ce matin ») need Prometheus `:9090` PromQL, not this endpoint. |
| `GET /monitoring/status` | « Le monitoring fonctionne-t-il ? A-t-on perdu des lignes de log ? Peut-on faire confiance au rapport de dérive ? » | read, safe | Distinct from /health on purpose: serving OK ≠ observability OK. Counter is **asynchronous** (flush thread): reading it right after a predict may lag by a few seconds. |
| `POST /reload` | « Un nouveau champion a été promu : recharge-le / mets l'API à jour. » | **mutating**, idempotent | The only call that changes system state → **human-in-the-loop confirmation** before executing. `reloaded=false` is a valid, non-error answer. |

## What the 7 endpoints CANNOT answer (→ scope for RAG + extra tools, later sprints)

- « Pourquoi la v2 a-t-elle été refusée par le gate ? » → `learning.md` / MLflow tags (`gate_result`) → **RAG + MLflow tool**.
- « Quel est le seuil de promotion ? » → `params.yaml` section `promote` → **RAG**.
- « Y a-t-il de la dérive cette semaine ? » → Postgres `monitoring.predictions` + Evidently → **tool** (`drift_report.py` wrapper).
- « Quelle expérience avait le meilleur val_acc ? » → MLflow tracking → **tool**.
- « Que veut dire l'angle mort du flou ? » → README section LIMITS → **RAG**.

The evaluation set (the portfolio differentiator) will pair each question with the
ground truth obtainable **from the API itself**, so answers are machine-checkable.
