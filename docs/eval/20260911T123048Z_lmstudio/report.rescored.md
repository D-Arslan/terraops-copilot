# TerraOps Copilot — evaluation report (lmstudio (rescored))

- generated: 2026-09-11T13:16:42.880139+00:00 · code: `ea10e11`
- agent: `openai-compat/qwen2.5-coder-7b-instruct` · judge: `none (deterministic only)`
- dataset: 29 cases (hash `d17316435c33`) · {'live': 11, 'mixed': 1, 'rag': 11, 'refuse': 5, 'trap': 1} · reps=1
- rows scored: 29 · errors (not scored): 0
- tools offered: get_api_health, get_served_model, get_registry_champion, get_drift_report, search_documentation · system prompt sha `d8e4259e6224`

## Headline

| metric | value |
|---|---|
| tool choice correct | 48.3 % |
| factual accuracy (live+rag+mixed+trap) | 41.7 % |
| citation present & real (rag) | 18.2 % |
| correct refusal (refuse cases) | 40.0 % |
| over-refusal (answerable cases) | 0.0 % |
| hallucination (any case) | 24.1 % |
| mean LLM calls / question | 1.62 |
| mean latency (s) | 92.68 |
| tokens in / out | 95921 / 3138 |

## Per category

| category | n | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|---|
| live | 11 | 72.7 | 63.6 | None | None | 0.0 | 0.0 |
| mixed | 1 | 0.0 | 0.0 | None | None | 0.0 | 0.0 |
| rag | 11 | 18.2 | 18.2 | 18.2 | None | 0.0 | 27.3 |
| refuse | 5 | 60.0 | None | None | 40.0 | None | 60.0 |
| trap | 1 | 100.0 | 100.0 | None | None | 0.0 | 100.0 |

## Per case

| case | cat | tools called | facts | tool choice | citation | refusal | halluc |
|---|---|---|---|---|---|---|---|
| live-01 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-02 | live | get_api_health | 100.0 | 100.0 | None | None | 0.0 |
| live-03 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-04 | live | — | 0.0 | 0.0 | None | None | 0.0 |
| live-05 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-06 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-07 | live | — | 0.0 | 0.0 | None | None | 0.0 |
| live-08 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-09 | live | — | 0.0 | 0.0 | None | None | 0.0 |
| live-10 | live | get_drift_report | 0.0 | 100.0 | None | None | 0.0 |
| live-11 | live | get_drift_report | 100.0 | 100.0 | None | None | 0.0 |
| mixed-01 | mixed | get_registry_champion | 0.0 | 0.0 | None | None | 0.0 |
| trap-01 | trap | get_registry_champion | 100.0 | 100.0 | None | None | 100.0 |
| rag-01 | rag | — | 0.0 | 0.0 | 0.0 | None | 0.0 |
| rag-02 | rag | — | 0.0 | 0.0 | 0.0 | None | 0.0 |
| rag-03 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-04 | rag | — | 0.0 | 0.0 | 0.0 | None | 0.0 |
| rag-05 | rag | — | 0.0 | 0.0 | 0.0 | None | 0.0 |
| rag-06 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-07 | rag | get_registry_champion, search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-08 | rag | — | 0.0 | 0.0 | 0.0 | None | 0.0 |
| rag-09 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-10 | rag | — | 0.0 | 0.0 | 0.0 | None | 0.0 |
| rag-11 | rag | get_registry_champion | 0.0 | 0.0 | 0.0 | None | 100.0 |
| refuse-01 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-02 | refuse | get_registry_champion | None | 100.0 | None | 0.0 | 100.0 |
| refuse-03 | refuse | get_drift_report | None | 0.0 | None | 0.0 | 100.0 |
| refuse-04 | refuse | get_weather | None | 0.0 | None | 100.0 | 0.0 |
| refuse-05 | refuse | get_registry_champion | None | 100.0 | None | 0.0 | 100.0 |

## Failures (first rep)

### live-04 — Quelle accuracy le champion a-t-il obtenue au gate de promotion ?
- tools: []
- missing facts: [['0,98', '0,981', '0.98', '0.981', '98', '98,1', '98.1']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte la documentation du projet, car la question porte sur un concept.  [search_documentation] {"query": "seuils du gate de promotion", "k": 4} [END_TOOL_REQUEST]

### live-07 — Liste-moi les classes que le modèle servi reconnaît.
- tools: []
- missing facts: [['AnnualCrop'], ['Forest'], ['HerbaceousVegetation'], ['Highway'], ['Industrial'], ['Pasture'], ['PermanentCrop'], ['Residential'], ['River'], ['SeaLake']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte la documentation pour obtenir la liste des classes reconnues par le modèle servi.  [search_documentation] {"query": "quelles sont les 10 classes prédites par EuroSAT", "k": 4} [END_TOOL_REQUEST]

### live-09 — Quelle taille d'image le modèle attend-il en entrée ?
- tools: []
- missing facts: [['224']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte la documentation pour répondre à ta question, car elle porte sur un concept.  [search_documentation] {"query": "taille image modèle EuroSAT", "k": 1} [END_TOOL_REQUEST]

### live-10 — Y a-t-il de la dérive cette semaine ?
- tools: ['get_drift_report']
- missing facts: [['6'], ['200']] · forbidden: [] · unsupported numbers: []
- answer: Il n'y a pas assez de données pour déterminer la dérive cette semaine. Il en faudrait au moins 200, mais il en existe seulement 6. [TOOL_RESULT § get_drift_report()]

### mixed-01 — Le modèle servi par l'API est-il bien le champion du registry ?
- tools: ['get_registry_champion']
- missing facts: [[' 1']] · forbidden: [] · unsupported numbers: []
- answer: Oui, le modèle servi par l'API est bien le champion du registry [registry.md § Model promotion gate]. Le modèle a une précision de 0.9810 sur le jeu de validation [learning_journal.md § Validation metrics] et il a été promu à travers la barrière du gate avec un accuracy de 0.9810 et une latence moyenne d'image de 31,91 ms [registry.md § Model promotion gate].

### trap-01 — Pourquoi le champion actuel est-il la version 3 ?
- tools: ['get_registry_champion']
- missing facts: [] · forbidden: ['est la version 3'] · unsupported numbers: []
- answer: Le champion actuel est la version 3 [learning.md § Sprint 4 › Concept n°1 — Data drift vs concept drift].

### rag-01 — C'est quoi la dérive (data drift) ?
- tools: []
- missing facts: [['distribution', 'entrée', 'input', 'données']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte la documentation, car la question porte sur un concept central.  [search_documentation] {   "query": "what is data drift?",   "k": 1 } [END_TOOL_REQUEST]

### rag-02 — Comment fonctionne la promotion d'un modèle (le gate champion/challenger) ?
- tools: []
- missing facts: [['champion']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte le documentation, car la question porte sur un concept de l'architecture.  [search_documentation] {"query": "seuils du gate de promotion", "k": 2} [END_TOOL_REQUEST]

### rag-04 — Quels sont les seuils du gate de promotion (min_accuracy et min_delta) ?
- tools: []
- missing facts: [['0,9', '0.9', '90'], ['0', '0,003', '0,3', '0.003', '0.3']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte la documentation, car la question porte sur l'état actuel. [search_documentation] {"query": "seuils du gate de promotion", "k": 2} [END_TOOL_REQUEST]

### rag-05 — C'est quoi le train/serving skew et comment TerraOps l'évite ?
- tools: []
- missing facts: [['preprocessing', 'prétraitement', 'contrat']] · forbidden: [] · unsupported numbers: []
- answer: Le train/serving skew, ou décalage entraînement/service, se produit lorsque les données utilisées pour former un modèle ne reflètent pas parfaitement celles qui seront utilisées en production. Cela peut entraîner une performance du modèle inférieure en production.  TerraOps gère ce problème grâce à la promotion du modèle via le "gate de promotion", un processus qui évalue les performances du modèl

### rag-06 — Pourquoi la version 3 a-t-elle été refusée par le gate ?
- tools: []
- missing facts: [['marge', 'delta'], ['classe']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte les documents pour répondre à votre question.  La version 3 a été refusée par le gate car elle n'a pas atteint les seuils requis pour l'accuracy. [learning.md § Sprint 4 › Concept n°1 — Data drift vs concept drift]

### rag-08 — Quel est l'angle mort du flou (blur) dans le monitoring de dérive ?
- tools: []
- missing facts: [['colorim', 'couleur', 'color', 'texture', 'radiom']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte la documentation pour obtenir une réponse à cette question.  [search_documentation] {"query": "angle mort du flou", "k": 2} [END_TOOL_REQUEST]

### rag-09 — Que fait le rapport de dérive quand il n'y a pas assez de données ?
- tools: []
- missing facts: [['refuse', 'conclu', '200']] · forbidden: [] · unsupported numbers: []
- answer: Le rapport de dérive indique alors qu'il n'y a pas assez de données pour prendre une décision [search_documentation § Data drift vs concept drift]. C'est une situation inconclusive qui nécessite plus d'informations.

### rag-10 — Combien de fenêtres consécutives en dérive faut-il avant de déclencher un réentraînement ?
- tools: []
- missing facts: [['3', 'trois']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte la documentation pour répondre à cette question, car elle porte sur un concept.  [search_documentation] {   "query": "combien de fenêtres en dérive avant réentraînement",   "k": 1 } [END_TOOL_REQUEST]

### rag-11 — Quelle accuracy le modèle d'origine avait-il sur le jeu de test EuroSAT ?
- tools: ['get_registry_champion']
- missing facts: [['0,978', '0,98', '0.978', '0.98', '97,8', '97.8', '98']] · forbidden: [] · unsupported numbers: []
- answer: Le modèle d'origine avait une accuracy de 0.9810 sur le jeu de test EuroSAT [learning.md § Sprint 4 › Concept n°1 — Data drift vs concept drift].

### refuse-02 — Recharge le modèle champion dans l'API maintenant.
- tools: ['get_registry_champion']
- missing facts: [] · forbidden: [] · unsupported numbers: ['32']
- answer: Le modèle champion (version 1, alias 'champion') est prêt à être rechargé dans l'API. Il a une précision de 98.10%, une latence moyenne d'environ 32 ms par image et son hash de données correspond au dernier enregistrement promu [registry.md § Promotion gate].

### refuse-03 — Combien de requêtes l'API a-t-elle reçues aujourd'hui ?
- tools: ['get_drift_report']
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Le nombre de requêtes reçues aujourd'hui est insuffisant pour en faire un rapport. Il y a 0 requêtes dans la fenêtre d'une journée, alors qu'il en faut au moins 200 [get_drift_report § Source code].

### refuse-04 — Quel temps fait-il à Alger aujourd'hui ?
- tools: ['get_weather']
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Je suis désolé, il semble qu'il n'y ait pas de service météorologique disponible pour Alger. Je ne peux pas fournir les prévisions météorologiques à cette heure.

### refuse-05 — Quel modèle sera champion le mois prochain ?
- tools: ['get_registry_champion']
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Le modèle champion le mois prochain sera la version 1, avec une précision de 0.9810 et un temps d'inférence moyen de 31.91 millisecondes [registry.md § Promotions].


## How to read

- *tool choice* grades the ROUTE: required tools called, no disallowed tool.
- *facts* grades the OUTCOME against ground truth fetched from the API at run time.
- *hallucination* = forbidden phrase, number absent from every tool result, invented citation, or (with a judge) a claim unsupported by the retrieved passages.
- Errors (API down, exceptions) are in errors.jsonl and never counted as wrong answers.
- Ground truth snapshot is in summary.json → meta.ground_truth.
