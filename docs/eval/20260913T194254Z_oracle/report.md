# TerraOps Copilot — evaluation report (oracle)

- generated: 2026-09-13T19:43:36.191362+00:00 · code: `1900e54-dirty`
- agent: `oracle/oracle` · judge: `none (deterministic only)`
- dataset: 29 cases (hash `d17316435c33`) · {'live': 11, 'mixed': 1, 'rag': 11, 'refuse': 5, 'trap': 1} · reps=1
- rows scored: 29 · errors (not scored): 0
- tools offered: get_api_health, get_served_model, get_registry_champion, get_drift_report, search_documentation · system prompt sha `d8e4259e6224`

## Headline

| metric | value |
|---|---|
| tool choice correct | 100.0 % |
| factual accuracy (live+rag+mixed+trap) | 100.0 % |
| citation present & real (rag) | 100.0 % |
| correct refusal (refuse cases) | 100.0 % |
| over-refusal (answerable cases) | 0.0 % |
| hallucination (any case) | 0.0 % |
| mean LLM calls / question | 1.83 |
| mean latency (s) | 0.68 |
| tokens in / out | 0 / 0 |

## Per category

| category | n | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|---|
| live | 11 | 100.0 | 100.0 | None | None | 0.0 | 0.0 |
| mixed | 1 | 100.0 | 100.0 | None | None | 0.0 | 0.0 |
| rag | 11 | 100.0 | 100.0 | 100.0 | None | 0.0 | 0.0 |
| refuse | 5 | 100.0 | None | None | 100.0 | None | 0.0 |
| trap | 1 | 100.0 | 100.0 | None | None | 0.0 | 0.0 |

## Per case

| case | cat | tools called | facts | tool choice | citation | refusal | halluc |
|---|---|---|---|---|---|---|---|
| live-01 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-02 | live | get_api_health | 100.0 | 100.0 | None | None | 0.0 |
| live-03 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-04 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-05 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-06 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-07 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-08 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-09 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-10 | live | get_drift_report | 100.0 | 100.0 | None | None | 0.0 |
| live-11 | live | get_drift_report | 100.0 | 100.0 | None | None | 0.0 |
| mixed-01 | mixed | get_registry_champion, get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| trap-01 | trap | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| rag-01 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-02 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-03 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-04 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-05 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-06 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-07 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-08 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-09 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-10 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-11 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| refuse-01 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-02 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-03 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-04 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-05 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |

## Failures (first rep)

(none)

## How to read

- *tool choice* grades the ROUTE: required tools called, no disallowed tool.
- *facts* grades the OUTCOME against ground truth fetched from the API at run time.
- *hallucination* = forbidden phrase, number absent from every tool result, invented citation, or (with a judge) a claim unsupported by the retrieved passages.
- Errors (API down, exceptions) are in errors.jsonl and never counted as wrong answers.
- Ground truth snapshot is in summary.json → meta.ground_truth.
