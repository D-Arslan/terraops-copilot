# TerraOps Copilot — evaluation report (lmstudio (rescored))

- generated: 2026-09-11T15:03:21.465558+00:00 · code: `c019c41`
- agent: `openai-compat/qwen2.5-3b-instruct` · judge: `none (deterministic only)`
- dataset: 29 cases (hash `d17316435c33`) · {'live': 11, 'mixed': 1, 'rag': 11, 'refuse': 5, 'trap': 1} · reps=1
- rows scored: 29 · errors (not scored): 0
- tools offered: get_api_health, get_served_model, get_registry_champion, get_drift_report, search_documentation · system prompt sha `d8e4259e6224`

## Headline

| metric | value |
|---|---|
| tool choice correct | 69.0 % |
| factual accuracy (live+rag+mixed+trap) | 54.2 % |
| citation present & real (rag) | 27.3 % |
| correct refusal (refuse cases) | 60.0 % |
| over-refusal (answerable cases) | 4.2 % |
| hallucination (any case) | 17.2 % |
| mean LLM calls / question | 1.93 |
| mean latency (s) | 45.64 |
| tokens in / out | 98832 / 5627 |

## Per category

| category | n | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|---|
| live | 11 | 81.8 | 72.7 | None | None | 0.0 | 0.0 |
| mixed | 1 | 0.0 | 100.0 | None | None | 0.0 | 0.0 |
| rag | 11 | 54.5 | 36.4 | 27.3 | None | 9.1 | 27.3 |
| refuse | 5 | 80.0 | None | None | 60.0 | None | 20.0 |
| trap | 1 | 100.0 | 0.0 | None | None | 0.0 | 100.0 |

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
| live-08 | live | get_api_health | 0.0 | 0.0 | None | None | 0.0 |
| live-09 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-10 | live | — | 0.0 | 0.0 | None | None | 0.0 |
| live-11 | live | get_drift_report | 0.0 | 100.0 | None | None | 0.0 |
| mixed-01 | mixed | get_registry_champion | 100.0 | 0.0 | None | None | 0.0 |
| trap-01 | trap | get_registry_champion | 0.0 | 100.0 | None | None | 100.0 |
| rag-01 | rag | search_documentation | 100.0 | 100.0 | 0.0 | None | 0.0 |
| rag-02 | rag | search_documentation | 100.0 | 100.0 | 0.0 | None | 0.0 |
| rag-03 | rag | search_documentation | 0.0 | 100.0 | 100.0 | None | 0.0 |
| rag-04 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-05 | rag | search_documentation | 100.0 | 100.0 | 100.0 | None | 0.0 |
| rag-06 | rag | get_registry_champion | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-07 | rag | get_registry_champion | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-08 | rag | — | 0.0 | 0.0 | 0.0 | None | 0.0 |
| rag-09 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-10 | rag | search_documentation | 0.0 | 100.0 | 0.0 | None | 0.0 |
| rag-11 | rag | get_registry_champion | 0.0 | 0.0 | 0.0 | None | 0.0 |
| refuse-01 | refuse | get_api_health, search_documentation | None | 0.0 | None | 100.0 | 0.0 |
| refuse-02 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-03 | refuse | get_api_health | None | 100.0 | None | 0.0 | 0.0 |
| refuse-04 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |
| refuse-05 | refuse | get_registry_champion | None | 100.0 | None | 0.0 | 100.0 |

## Failures (first rep)

### live-08 — Sur quel device (CPU ou GPU) tourne l'inférence ?
- tools: ['get_api_health']
- missing facts: [['cpu']] · forbidden: [] · unsupported numbers: []
- answer: Sur le serveur actuel, l'inference tourne sur GPU. Le modèle est chargé et la version 1 est en vigueur.

### live-10 — Y a-t-il de la dérive cette semaine ?
- tools: []
- missing facts: [['6'], ['200']] · forbidden: [] · unsupported numbers: []
- answer: 

### live-11 — Combien de prédictions ont été journalisées ces 7 derniers jours ?
- tools: ['get_drift_report']
- missing facts: [['6']] · forbidden: [] · unsupported numbers: []
- answer: Il y a eu moins de 200 prédictions journalisées dans la fenêtre de temps de 7 jours. Il n'y a pas assez d'informations disponibles pour fournir une estimation précise actuelle.

### mixed-01 — Le modèle servi par l'API est-il bien le champion du registry ?
- tools: ['get_registry_champion']
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Le modèle servant l'API est bien le champion du registry, version 1 qui a obtenu un score de précision de 0.9810 lors du gate promotionnel et qui n'a pas subi de changement depuis son dernier passage dans ce rôle.

### trap-01 — Pourquoi le champion actuel est-il la version 3 ?
- tools: ['get_registry_champion']
- missing facts: [['version 1', 'v1', 'la 1', 'numéro 1', 'version: 1', 'version 1 ']] · forbidden: ['est la version 3'] · unsupported numbers: []
- answer: Le champion actuel est la version 3 car elle a obtenu un taux de précision de 0.9810 lors du gate promotionnel, ce qui lui a permis d'être promu et de prendre le rôle de modèle courant.

### rag-03 — Pourquoi TerraOps utilise Wasserstein plutôt qu'un test à p-value ?
- tools: ['search_documentation']
- missing facts: [['volume', 'taille', 'effet', 'effect', 'échantillon', 'n =']] · forbidden: [] · unsupported numbers: []
- answer: Selon les notes de paramétrage dans [params.yaml § params.yaml], TerraOps utilise l'indicateur Wasserstein plutôt que le test à p-value car il répond « par combien » et non simplement à si une différence existe. C'est expliqué en détail dans la documentation du projet : [learning.md § Concept 5 — Principe de Wasserstein vs Test à p].

### rag-06 — Pourquoi la version 3 a-t-elle été refusée par le gate ?
- tools: ['get_registry_champion']
- missing facts: [['marge', 'delta'], ['classe']] · forbidden: [] · unsupported numbers: ['0.1']
- answer: Je rencontre une erreur car le numéro de version n'est pas correct. Veuillez me fournir une version valide pour que je puisse examiner pourquoi elle a été rejetée par le gate. Un exemple d'une version est "0.1".

### rag-07 — Quelle accuracy la version 4 avait-elle au gate, et pourquoi a-t-elle été refusée ?
- tools: ['get_registry_champion']
- missing facts: [['0,9765', '0,977', '0,98', '0.9765', '0.977', '0.98', '97,65', '97,7', '97.65', '97.7', '98'], ['marge', 'delta', '0.44', '0,44']] · forbidden: [] · unsupported numbers: []
- answer: La version 4 du modèle avait une accuracy de [learning.md § Sprint 4 › Concept n°2 — Accuracy thresholds for promotion gate] = 0.9810 lorsqu'elle a été soumise au gate de promotion. Elle s'est pourtant vu refuser, ce qui est conforme à la règle fixée par le gate : [learning.md § Sprint 4 › Concept n°3 — How the Champion is selected and why we use an accuracy threshold]

### rag-08 — Quel est l'angle mort du flou (blur) dans le monitoring de dérive ?
- tools: []
- missing facts: [['colorim', 'couleur', 'color', 'texture', 'radiom']] · forbidden: [] · unsupported numbers: []
- answer: Je ne trouve pas de documentation spécifique à ce sujet. Nommez ce dont vous auriez besoin pour répondre.

### rag-09 — Que fait le rapport de dérive quand il n'y a pas assez de données ?
- tools: []
- missing facts: [['refuse', 'conclu', '200']] · forbidden: [] · unsupported numbers: ['3.1']
- answer: [live.md § 3.1.2 — Si la taille du lot de trafic récent est insuffisante pour faire un jugement sur les différences, le rapport de dérive retournera "inconclusive".]

### rag-10 — Combien de fenêtres consécutives en dérive faut-il avant de déclencher un réentraînement ?
- tools: ['search_documentation']
- missing facts: [['3', 'trois']] · forbidden: [] · unsupported numbers: []
- answer: Selon les notes de démonstration de la sprint 4, un plafond de fenêtre est appliqué à 2000 jours consécutifs avant de réentraîner. Il n'y a pas de seuil de refus spécifique mentionné pour le nombre de fenêtres consécutives en dérive nécessaires, mais il est mentionné qu'il existe un plafond de fenêtre de 2000 jours.

### rag-11 — Quelle accuracy le modèle d'origine avait-il sur le jeu de test EuroSAT ?
- tools: ['get_registry_champion']
- missing facts: [['0,978', '0,98', '0.978', '0.98', '97,8', '97.8', '98']] · forbidden: [] · unsupported numbers: []
- answer: Je ne peux pas trouver les informations sur l'accuracy du modèle d'origine. Il faut utiliser get_registry_champion pour obtenir la précision de la version champion, qui est le modèle actuellement en service.

### refuse-01 — Quelle est la latence p95 de l'API sur la dernière heure ?
- tools: ['get_api_health', 'search_documentation']
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Selon la documentation TerraOps, il semble qu'il existe une règle Prometheus qui peut être utilisée pour déterminer si l'API a des latences de prédiction supérieures à 400ms, ce qui serait considéré comme un seuil critique. Cependant, les outils actuels n'étaient pas capables d'obtenir le p95 spécifique.  La règle Prometheus est définie dans `prometheus_rules.yml` et elle utilise la quantile de l'

### refuse-03 — Combien de requêtes l'API a-t-elle reçues aujourd'hui ?
- tools: ['get_api_health']
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Il semble que l'API ne fournisse pas directement la quantité de requêtes reçues aujourd'hui. Je vais utiliser un autre outil pour obtenir cette information.

### refuse-05 — Quel modèle sera champion le mois prochain ?
- tools: ['get_registry_champion']
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Le champion du mois prochain sera la version 1 de 'terraops-eurosat', qui a obtenu une précision de 98,10% lors des tests.


## How to read

- *tool choice* grades the ROUTE: required tools called, no disallowed tool.
- *facts* grades the OUTCOME against ground truth fetched from the API at run time.
- *hallucination* = forbidden phrase, number absent from every tool result, invented citation, or (with a judge) a claim unsupported by the retrieved passages.
- Errors (API down, exceptions) are in errors.jsonl and never counted as wrong answers.
- Ground truth snapshot is in summary.json → meta.ground_truth.
