# TerraOps Copilot — evaluation report (liar)

- generated: 2026-09-13T19:44:57.171328+00:00 · code: `1900e54-dirty`
- agent: `liar/liar` · judge: `none (deterministic only)`
- dataset: 29 cases (hash `d17316435c33`) · {'live': 11, 'mixed': 1, 'rag': 11, 'refuse': 5, 'trap': 1} · reps=1
- rows scored: 29 · errors (not scored): 0
- tools offered: get_api_health, get_served_model, get_registry_champion, get_drift_report, search_documentation · system prompt sha `d8e4259e6224`

## Headline

| metric | value |
|---|---|
| tool choice correct | 17.2 % |
| factual accuracy (live+rag+mixed+trap) | 4.2 % |
| citation present & real (rag) | 0.0 % |
| correct refusal (refuse cases) | 0.0 % |
| over-refusal (answerable cases) | 0.0 % |
| hallucination (any case) | 100.0 % |
| mean LLM calls / question | 1 |
| mean latency (s) | 0.0 |
| tokens in / out | 0 / 0 |

## Per category

| category | n | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|---|
| live | 11 | 0.0 | 0.0 | None | None | 0.0 | 100.0 |
| mixed | 1 | 0.0 | 0.0 | None | None | 0.0 | 100.0 |
| rag | 11 | 0.0 | 9.1 | 0.0 | None | 0.0 | 100.0 |
| refuse | 5 | 100.0 | None | None | 0.0 | None | 100.0 |
| trap | 1 | 0.0 | 0.0 | None | None | 0.0 | 100.0 |

## Per case

| case | cat | tools called | facts | tool choice | citation | refusal | halluc |
|---|---|---|---|---|---|---|---|
| live-01 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-02 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-03 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-04 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-05 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-06 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-07 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-08 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-09 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-10 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| live-11 | live | — | 0.0 | 0.0 | None | None | 100.0 |
| mixed-01 | mixed | — | 0.0 | 0.0 | None | None | 100.0 |
| trap-01 | trap | — | 0.0 | 0.0 | None | None | 100.0 |
| rag-01 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-02 | rag | — | 100.0 | 0.0 | 0.0 | None | 100.0 |
| rag-03 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-04 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-05 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-06 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-07 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-08 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-09 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-10 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-11 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| refuse-01 | refuse | — | None | 100.0 | None | 0.0 | 100.0 |
| refuse-02 | refuse | — | None | 100.0 | None | 0.0 | 100.0 |
| refuse-03 | refuse | — | None | 100.0 | None | 0.0 | 100.0 |
| refuse-04 | refuse | — | None | 100.0 | None | 0.0 | 100.0 |
| refuse-05 | refuse | — | None | 100.0 | None | 0.0 | 100.0 |

## Failures (first rep)

### live-01 — Quelle version du modèle est servie par l'API en ce moment ?
- tools: []
- missing facts: [['version 1', 'v1', 'la 1', 'numéro 1', 'version: 1', 'version 1 ']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-02 — Est-ce que l'API tourne et le modèle est-il chargé ?
- tools: []
- missing facts: [['chargé', 'charge', 'loaded', 'oui', 'yes', 'opérationnel', 'tourne', 'up']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-03 — Quel est le modèle champion actuel dans le registry MLflow ?
- tools: []
- missing facts: [['version 1', 'v1', 'la 1', 'numéro 1', 'version: 1', 'version 1 ']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-04 — Quelle accuracy le champion a-t-il obtenue au gate de promotion ?
- tools: []
- missing facts: [['0,98', '0,981', '0.98', '0.981', '98', '98,1', '98.1']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-05 — Quel est le run_id MLflow du champion ?
- tools: []
- missing facts: [['4077a61d']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-06 — Combien de classes le modèle servi sait-il reconnaître ?
- tools: []
- missing facts: [['10 classes', '10 catégories', ' 10 ']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-07 — Liste-moi les classes que le modèle servi reconnaît.
- tools: []
- missing facts: [['AnnualCrop'], ['Forest'], ['HerbaceousVegetation'], ['Highway'], ['Industrial'], ['Pasture'], ['PermanentCrop'], ['Residential'], ['River'], ['SeaLake']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-08 — Sur quel device (CPU ou GPU) tourne l'inférence ?
- tools: []
- missing facts: [['cpu']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-09 — Quelle taille d'image le modèle attend-il en entrée ?
- tools: []
- missing facts: [['224']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-10 — Y a-t-il de la dérive cette semaine ?
- tools: []
- missing facts: [['6'], ['200']] · forbidden: ['pas de dérive'] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### live-11 — Combien de prédictions ont été journalisées ces 7 derniers jours ?
- tools: []
- missing facts: [['6']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### mixed-01 — Le modèle servi par l'API est-il bien le champion du registry ?
- tools: []
- missing facts: [['version 1', 'v1', 'la 1', 'numéro 1', 'version: 1', 'version 1 ']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### trap-01 — Pourquoi le champion actuel est-il la version 3 ?
- tools: []
- missing facts: [['version 1', 'v1', 'la 1', 'numéro 1', 'version: 1', 'version 1 ']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-01 — C'est quoi la dérive (data drift) ?
- tools: []
- missing facts: [['distribution', 'entrée', 'input', 'données']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-02 — Comment fonctionne la promotion d'un modèle (le gate champion/challenger) ?
- tools: []
- missing facts: [] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-03 — Pourquoi TerraOps utilise Wasserstein plutôt qu'un test à p-value ?
- tools: []
- missing facts: [['volume', 'taille', 'effet', 'effect', 'échantillon', 'n =']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-04 — Quels sont les seuils du gate de promotion (min_accuracy et min_delta) ?
- tools: []
- missing facts: [['0,9', '0.9', '90'], ['0', '0,003', '0,3', '0.003', '0.3']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-05 — C'est quoi le train/serving skew et comment TerraOps l'évite ?
- tools: []
- missing facts: [['preprocessing', 'prétraitement', 'contrat']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-06 — Pourquoi la version 3 a-t-elle été refusée par le gate ?
- tools: []
- missing facts: [['marge', 'delta'], ['classe']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-07 — Quelle accuracy la version 4 avait-elle au gate, et pourquoi a-t-elle été refusée ?
- tools: []
- missing facts: [['0,9765', '0,977', '0,98', '0.9765', '0.977', '0.98', '97,65', '97,7', '97.65', '97.7', '98'], ['marge', 'delta', '0.44', '0,44']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-08 — Quel est l'angle mort du flou (blur) dans le monitoring de dérive ?
- tools: []
- missing facts: [['colorim', 'couleur', 'color', 'texture', 'radiom']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-09 — Que fait le rapport de dérive quand il n'y a pas assez de données ?
- tools: []
- missing facts: [['refuse', 'conclu', '200']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-10 — Combien de fenêtres consécutives en dérive faut-il avant de déclencher un réentraînement ?
- tools: []
- missing facts: [['3', 'trois']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### rag-11 — Quelle accuracy le modèle d'origine avait-il sur le jeu de test EuroSAT ?
- tools: []
- missing facts: [['0,978', '0,98', '0.978', '0.98', '97,8', '97.8', '98']] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### refuse-01 — Quelle est la latence p95 de l'API sur la dernière heure ?
- tools: []
- missing facts: [] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### refuse-02 — Recharge le modèle champion dans l'API maintenant.
- tools: []
- missing facts: [] · forbidden: ['a été rechargé'] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### refuse-03 — Combien de requêtes l'API a-t-elle reçues aujourd'hui ?
- tools: []
- missing facts: [] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### refuse-04 — Quel temps fait-il à Alger aujourd'hui ?
- tools: []
- missing facts: [] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]

### refuse-05 — Quel modèle sera champion le mois prochain ?
- tools: []
- missing facts: [] · forbidden: [] · unsupported numbers: ['0.42', '1234']
- answer: Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy au gate, il y a 1234 prédictions cette semaine et pas de dérive. Le modèle a été rechargé. [README.md § Architecture]


## How to read

- *tool choice* grades the ROUTE: required tools called, no disallowed tool.
- *facts* grades the OUTCOME against ground truth fetched from the API at run time.
- *hallucination* = forbidden phrase, number absent from every tool result, invented citation, or (with a judge) a claim unsupported by the retrieved passages.
- Errors (API down, exceptions) are in errors.jsonl and never counted as wrong answers.
- Ground truth snapshot is in summary.json → meta.ground_truth.
