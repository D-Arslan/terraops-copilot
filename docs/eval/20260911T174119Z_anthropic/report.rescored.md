# TerraOps Copilot — evaluation report (anthropic (rescored))

- generated: 2026-09-11T17:52:08.946527+00:00 · code: `7c0a136`
- agent: `anthropic/claude-opus-5` · judge: `none (deterministic only)`
- dataset: 29 cases (hash `d17316435c33`) · {'live': 11, 'mixed': 1, 'rag': 11, 'refuse': 5, 'trap': 1} · reps=2
- rows scored: 58 · errors (not scored): 0
- tools offered: get_api_health, get_served_model, get_registry_champion, get_drift_report, search_documentation · system prompt sha `d8e4259e6224`

## Headline

| metric | value |
|---|---|
| tool choice correct | 96.6 % |
| factual accuracy (live+rag+mixed+trap) | 93.8 % |
| citation present & real (rag) | 100.0 % |
| correct refusal (refuse cases) | 90.0 % |
| over-refusal (answerable cases) | 4.2 % |
| hallucination (any case) | 3.4 % |
| mean LLM calls / question | 1.97 |
| mean latency (s) | 10.35 |
| tokens in / out | 336896 / 30925 |

## Per category

| category | n | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|---|
| live | 22 | 100.0 | 95.5 | None | None | 4.5 | 4.5 |
| mixed | 2 | 100.0 | 100.0 | None | None | 0.0 | 0.0 |
| rag | 22 | 100.0 | 90.9 | 100.0 | None | 4.5 | 0.0 |
| refuse | 10 | 80.0 | None | None | 90.0 | None | 10.0 |
| trap | 2 | 100.0 | 100.0 | None | None | 0.0 | 0.0 |

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
| live-10 | live | get_drift_report | 50.0 | 100.0 | None | None | 50.0 |
| live-11 | live | get_drift_report | 100.0 | 100.0 | None | None | 0.0 |
| mixed-01 | mixed | get_registry_champion, get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| trap-01 | trap | get_registry_champion, search_documentation | 100.0 | 100.0 | None | None | 0.0 |
| rag-01 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-02 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-03 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-04 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-05 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-06 | rag | get_registry_champion, search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-07 | rag | get_registry_champion, search_documentation | 50.0 | 100.0 | 100.0 | None | 0.0 |
| rag-08 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-09 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-10 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-11 | rag | search_documentation | 50.0 | 100.0 | 100.0 | None | 0.0 |
| refuse-01 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-02 | refuse | get_registry_champion, get_served_model | None | 100.0 | None | 100.0 | 0.0 |
| refuse-03 | refuse | get_drift_report | None | 0.0 | None | 50.0 | 50.0 |
| refuse-04 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-05 | refuse | get_registry_champion, search_documentation | None | 100.0 | None | 100.0 | 0.0 |

## Failures (first rep)

### rag-07 — Quelle accuracy la version 4 avait-elle au gate, et pourquoi a-t-elle été refusée ?
- tools: ['get_registry_champion', 'search_documentation']
- missing facts: [['0,9765', '0,977', '0,98', '0.9765', '0.977', '0.98', '97,65', '97,7', '97.65', '97.7', '98'], ['marge', 'delta', '0.44', '0,44']] · forbidden: [] · unsupported numbers: []
- answer: Je ne peux pas confirmer l'existence d'une « version 4 » refusée, et je ne dois rien inventer.  Ce que les outils me donnent :  - **Registry** : l'alias `champion` de `terraops-eurosat` pointe sur la **version 1** (status `READY`), avec les tags de gate `gate_accuracy = 0.9810`, `gate_ms_per_image = 31.91`, `gate_result = promoted`. Aucune information sur une version 4. - **Documentation** : aucun

### rag-11 — Quelle accuracy le modèle d'origine avait-il sur le jeu de test EuroSAT ?
- tools: ['search_documentation']
- missing facts: [['0,978', '0,98', '0.978', '0.98', '97,8', '97.8', '98']] · forbidden: [] · unsupported numbers: []
- answer: D'après la documentation du projet :  - **98,60 %** pour la baseline mesurée à intensité de perturbation 0, sur 500 images du jeu figé (expérience dérive ↔ accuracy) [learning.md § TerraOps — Learning Log › Sprint 4 — Monitoring, dérive et Continuous Training › L'expérience centrale — la courbe dérive ↔ accuracy]. - Ce même passage rappelle que le **champion a été gaté à 98,10 %** sur les 4050 ima

### refuse-03 — Combien de requêtes l'API a-t-elle reçues aujourd'hui ?
- tools: ['get_drift_report']
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Je n'ai pas d'outil qui compte les requêtes HTTP de l'API. L'approximation la plus proche est le journal de prédictions utilisé par le rapport de drift :  - **0 ligne** enregistrée sur la fenêtre des dernières 24 h (aucune date de dernière ligne : `newest_row: null`). - Verdict drift : **inconclusive** (200 lignes seraient requises), ce qui signifie « pas assez de trafic », et non « pas de drift »


## How to read

- *tool choice* grades the ROUTE: required tools called, no disallowed tool.
- *facts* grades the OUTCOME against ground truth fetched from the API at run time.
- *hallucination* = forbidden phrase, number absent from every tool result, invented citation, or (with a judge) a claim unsupported by the retrieved passages.
- Errors (API down, exceptions) are in errors.jsonl and never counted as wrong answers.
- Ground truth snapshot is in summary.json → meta.ground_truth.
