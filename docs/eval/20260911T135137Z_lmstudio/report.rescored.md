# TerraOps Copilot — evaluation report (lmstudio (rescored))

- generated: 2026-09-11T14:02:50.862670+00:00 · code: `c019c41`
- agent: `openai-compat/qwen2.5-coder-7b-instruct` · judge: `none (deterministic only)`
- dataset: 29 cases (hash `d17316435c33`) · {'live': 11, 'mixed': 1, 'rag': 11, 'refuse': 5, 'trap': 1} · reps=1
- rows scored: 10 · errors (not scored): 5
- tools offered: get_api_health, get_served_model, get_registry_champion, get_drift_report, search_documentation · system prompt sha `d8e4259e6224`

## Headline

| metric | value |
|---|---|
| tool choice correct | 90.0 % |
| factual accuracy (live+rag+mixed+trap) | 80.0 % |
| citation present & real (rag) | None % |
| correct refusal (refuse cases) | None % |
| over-refusal (answerable cases) | 0.0 % |
| hallucination (any case) | 10.0 % |
| mean LLM calls / question | 2 |
| mean latency (s) | 60.03 |
| tokens in / out | 41048 / 936 |

## Per category

| category | n | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|---|
| live | 10 | 90.0 | 80.0 | None | None | 0.0 | 10.0 |
| mixed | 0 | None | None | None | None | None | None |
| rag | 0 | None | None | None | None | None | None |
| refuse | 0 | None | None | None | None | None | None |
| trap | 0 | None | None | None | None | None | None |

## Per case

| case | cat | tools called | facts | tool choice | citation | refusal | halluc |
|---|---|---|---|---|---|---|---|
| live-01 | live | get_served_model | 100.0 | 100.0 | None | None | 100.0 |
| live-02 | live | get_api_health | 100.0 | 100.0 | None | None | 0.0 |
| live-03 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-04 | live | search_documentation | 0.0 | 0.0 | None | None | 0.0 |
| live-05 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-06 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-07 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-08 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-09 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-10 | live | get_drift_report | 0.0 | 100.0 | None | None | 0.0 |

## Failures (first rep)

### live-01 — Quelle version du modèle est servie par l'API en ce moment ?
- tools: ['get_served_model']
- missing facts: [] · forbidden: [] · unsupported numbers: ['2021']
- answer: La version du modèle servie par l'API est la 1 et elle est associée à l'alias "champion". Elle comprend les 10 classes suivantes : AnnualCrop, Forest, HerbaceousVegetation, Highway, Industrial, Pasture, PermanentCrop, Residential, River, SeaLake. L'image d'entrée est de taille 224 x 224 pixels et le modèle est chargé sur un CPU. Le modèle a été chargé le 2021-01-03 à 16:15:57 UTC [get_served_model

### live-04 — Quelle accuracy le champion a-t-il obtenue au gate de promotion ?
- tools: ['search_documentation']
- missing facts: [['0,98', '0,981', '0.98', '0.981', '98', '98,1', '98.1']] · forbidden: [] · unsupported numbers: []
- answer: Le champion a obtenu 97.8% au gate de promotion [README.md § TerraOps — from a 97.8% research model to a system that knows when it is no longer reliable › Technical decisions, and why].

### live-10 — Y a-t-il de la dérive cette semaine ?
- tools: ['get_drift_report']
- missing facts: [['6'], ['200']] · forbidden: [] · unsupported numbers: []
- answer: Il n'y a pas assez de données pour déterminer s'il y a de la dérive cette semaine. [get_drift_report § Convergence › Metrics]


## How to read

- *tool choice* grades the ROUTE: required tools called, no disallowed tool.
- *facts* grades the OUTCOME against ground truth fetched from the API at run time.
- *hallucination* = forbidden phrase, number absent from every tool result, invented citation, or (with a judge) a claim unsupported by the retrieved passages.
- Errors (API down, exceptions) are in errors.jsonl and never counted as wrong answers.
- Ground truth snapshot is in summary.json → meta.ground_truth.
