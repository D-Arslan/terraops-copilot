# TerraOps Copilot — evaluation report (lmstudio)

- generated: 2026-09-11T10:55:33.587497+00:00 · code: `bc5d901`
- agent: `openai-compat/qwen2.5-coder-7b-instruct` · judge: `none (deterministic only)`
- dataset: 29 cases (hash `d17316435c33`) · {'live': 11, 'mixed': 1, 'rag': 11, 'refuse': 5, 'trap': 1} · reps=2
- rows scored: 50 · errors (not scored): 8
- tools offered: get_api_health, get_served_model, get_registry_champion, get_drift_report, search_documentation · system prompt sha `c1c5e18ece53`

## Headline

| metric | value |
|---|---|
| tool choice correct | 56.0 % |
| factual accuracy (live+rag+mixed+trap) | 52.1 % |
| citation present & real (rag) | 9.1 % |
| correct refusal (refuse cases) | 100.0 % |
| over-refusal (answerable cases) | 6.2 % |
| hallucination (any case) | 24.0 % |
| mean LLM calls / question | 1.72 |
| mean latency (s) | 88.87 |
| tokens in / out | 170915 / 6611 |

## Per category

| category | n | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|---|
| live | 22 | 95.5 | 77.3 | None | None | 0.0 | 0.0 |
| mixed | 2 | 0.0 | 50.0 | None | None | 0.0 | 0.0 |
| rag | 22 | 13.6 | 27.3 | 9.1 | None | 13.6 | 54.5 |
| refuse | 2 | 100.0 | None | None | 100.0 | None | 0.0 |
| trap | 2 | 100.0 | 50.0 | None | None | 0.0 | 0.0 |

## Per case

| case | cat | tools called | facts | tool choice | citation | refusal | halluc |
|---|---|---|---|---|---|---|---|
| live-01 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-02 | live | get_api_health | 100.0 | 100.0 | None | None | 0.0 |
| live-03 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-04 | live | get_registry_champion | 0.0 | 100.0 | None | None | 0.0 |
| live-05 | live | get_registry_champion | 100.0 | 100.0 | None | None | 0.0 |
| live-06 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-07 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-08 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-09 | live | get_served_model | 100.0 | 100.0 | None | None | 0.0 |
| live-10 | live | get_drift_report | 0.0 | 50.0 | None | None | 0.0 |
| live-11 | live | get_drift_report | 50.0 | 100.0 | None | None | 0.0 |
| mixed-01 | mixed | get_api_health, get_registry_champion | 50.0 | 0.0 | None | None | 0.0 |
| trap-01 | trap | get_registry_champion | 50.0 | 100.0 | None | None | 0.0 |
| rag-01 | rag | — | 100.0 | 0.0 | 0.0 | None | 50.0 |
| rag-02 | rag | — | 100.0 | 0.0 | 0.0 | None | 100.0 |
| rag-03 | rag | — | 50.0 | 0.0 | 0.0 | None | 100.0 |
| rag-04 | rag | search_documentation | 0.0 | 50.0 | 0.0 | None | 0.0 |
| rag-05 | rag | — | 0.0 | 0.0 | 0.0 | None | 50.0 |
| rag-06 | rag | get_registry_champion | 0.0 | 0.0 | 0.0 | None | 50.0 |
| rag-07 | rag | get_registry_champion | 0.0 | 0.0 | 0.0 | None | 0.0 |
| rag-08 | rag | search_documentation | 0.0 | 100.0 | 100.0 | None | 0.0 |
| rag-09 | rag | — | 0.0 | 0.0 | 0.0 | None | 100.0 |
| rag-10 | rag | — | 50.0 | 0.0 | 0.0 | None | 100.0 |
| rag-11 | rag | — | 0.0 | 0.0 | 0.0 | None | 50.0 |
| refuse-01 | refuse | — | None | 100.0 | None | 100.0 | 0.0 |

## Failures (first rep)

### live-04 — Quelle accuracy le champion a-t-il obtenue au gate de promotion ?
- tools: ['get_registry_champion']
- missing facts: [['0,98', '0,981', '0.98', '0.981', '98', '98,1', '98.1']] · forbidden: [] · unsupported numbers: []
- answer: Le champion a obtenu une accuracy de 0.9810 au gate de promotion [source § section].

### live-10 — Y a-t-il de la dérive cette semaine ?
- tools: ['get_drift_report']
- missing facts: [['200']] · forbidden: [] · unsupported numbers: []
- answer: Il n'y a pas assez de données pour déterminer la dérive cette semaine. Néanmoins, il y a eu 6 interactions avec le modèle ces derniers jours. Pour obtenir un verdict fiable, plus de données sont nécessaires. [source § drift report]

### live-11 — Combien de prédictions ont été journalisées ces 7 derniers jours ?
- tools: ['get_drift_report']
- missing facts: [['6']] · forbidden: [] · unsupported numbers: []
- answer: Il n'y a pas assez de données pour déterminer s'il y a une dérive. Il faut au moins 200 prédictions journalisées ces 7 derniers jours. [source § drift_report]

### mixed-01 — Le modèle servi par l'API est-il bien le champion du registry ?
- tools: ['get_registry_champion']
- missing facts: [[' 1']] · forbidden: [] · unsupported numbers: []
- answer: Le modèle servi par l'API est bien le champion du registry [source § section].

### trap-01 — Pourquoi le champion actuel est-il la version 3 ?
- tools: ['get_registry_champion', 'get_registry_champion', 'get_registry_champion', 'get_registry_champion', 'get_registry_champion']
- missing facts: [['version 1', 'v1', ' 1']] · forbidden: [] · unsupported numbers: []
- answer: Il semble qu'il y ait une erreur. La version du champion actuellement affichée est la 1, mais la question porte sur la version 3.  Je consulte à nouveau le registry pour confirmer. [TOOL_REQUEST] {"name": "get_registry_champion", "arguments": {}} [END_TOOL_REQUEST]

### rag-01 — C'est quoi la dérive (data drift) ?
- tools: []
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: La dérive (data drift) est un phénomène qui se produit lorsqu'il y a une différence significative entre les données d'entraînement et celles utilisées pour faire des prédictions. Cela peut entraîner une performance dégradée du modèle en production, car il ne fonctionne plus comme prévu avec de nouvelles données.  Cette dérive est généralement due à plusieurs facteurs : - **Collecte de données non 

### rag-02 — Comment fonctionne la promotion d'un modèle (le gate champion/challenger) ?
- tools: []
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Je consulte la documentation pour répondre à ta question.  La promotion d'un modèle au niveau du "champion" dans TerraOps est un processus formel qui vérifie si un nouveau modèle ("challenger") dépose une performance supérieure à un certain seuil défini par le "gate champion". Si les tests réussissent, le modèle challenger devient le nouveau champion. Cependant, la promotion n'est effectuée que ap

### rag-03 — Pourquoi TerraOps utilise Wasserstein plutôt qu'un test à p-value ?
- tools: []
- missing facts: [['volume', 'taille', 'effet', 'effect', 'échantillon', 'n =']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte les documents de TerraOps pour répondre à cette question.  [Wasserstein distance] est préférée aux tests à [p-value] dans TerraOps car elle permet une compréhension plus intuitive et géométrique des différences entre deux distributions, ce qui est particulièrement utile lorsqu'on analyse les changements de distribution en données d'images satellites. De plus, la Wasserstein distance pr

### rag-04 — Quels sont les seuils du gate de promotion (min_accuracy et min_delta) ?
- tools: ['search_documentation']
- missing facts: [['0,9', '0.9', '90'], ['0', '0,003', '0,3', '0.003', '0.3']] · forbidden: [] · unsupported numbers: []
- answer: Je suis désolé, mais les passages fournis ne contiennent pas directement les seuils du gate de promotion (`min_accuracy` et `min_delta`). Les passages discutent des concepts généraux du gate de promotion et mentionnent des règles, mais ils ne spécifient pas explicitement les valeurs exactes.  Je vous recommande de consulter la documentation complète pour obtenir ces informations précises.

### rag-05 — C'est quoi le train/serving skew et comment TerraOps l'évite ?
- tools: []
- missing facts: [['preprocessing', 'prétraitement', 'contrat']] · forbidden: [] · unsupported numbers: []
- answer: Le train/serving skew, aussi appelé gap d'entraînement/service, se produit lorsqu'il existe une différence entre les données utilisées pour former un modèle et celles qui sont utilisées au moment de la prédiction. Cela peut entraîner des performances moindres ou mauvaises sur les nouveaux exemples.  TerraOps évite ce skew en adoptant plusieurs stratégies :  1. **Modèles multiversion** : TerraOps m

### rag-06 — Pourquoi la version 3 a-t-elle été refusée par le gate ?
- tools: []
- missing facts: [['marge', 'delta'], ['classe']] · forbidden: [] · unsupported numbers: []
- answer: Je consulte le registre, car la question porte sur l'état actuel. Le modèle v3 a été refusé par le gate de promotion car sa performance n'a pas atteint les seuils requis. Les détails précis de la décision sont disponibles dans la documentation du processus de promotion [source § Promotion Process].

### rag-07 — Quelle accuracy la version 4 avait-elle au gate, et pourquoi a-t-elle été refusée ?
- tools: ['get_registry_champion']
- missing facts: [['0,9765', '0,977', '0,98', '0.9765', '0.977', '0.98', '97,65', '97,7', '97.65', '97.7', '98'], ['marge', 'delta', '0.44', '0,44']] · forbidden: [] · unsupported numbers: []
- answer: La version 4 a eu une accuracy de 0.9810 au gate et a été refusée parce qu'elle n'a pas atteint le seuil requis pour la promotion.

### rag-08 — Quel est l'angle mort du flou (blur) dans le monitoring de dérive ?
- tools: ['search_documentation']
- missing facts: [['colorim', 'couleur', 'color', 'texture', 'radiom']] · forbidden: [] · unsupported numbers: []
- answer: L'angle mort du flou dans le monitoring de dérive est structural. Selon la documentation : "Le flou est un angle mort STRUCTUREL. L'accuracy tombe 97 → 81 → 61 % avec une part en dérive à **0.00**." [learning.md § TerraOps — Learning Log › Sprint 4 — Monitoring, dérive et Continuous Training › L'expérience centrale — la courbe dérive ↔ accuracy]

### rag-09 — Que fait le rapport de dérive quand il n'y a pas assez de données ?
- tools: []
- missing facts: [['refuse', 'conclu', '200']] · forbidden: [] · unsupported numbers: []
- answer: Le rapport de dérive retourne une erreur ou un verdict "inconclusif" lorsque le nombre de données est insuffisant pour prendre une décision [source § drift.md#drift-report]. Cela signifie qu'il n'y a pas assez d'informations pour déterminer s'il y a ou non une dérive.

### rag-10 — Combien de fenêtres consécutives en dérive faut-il avant de déclencher un réentraînement ?
- tools: []
- missing facts: [] · forbidden: [] · unsupported numbers: []
- answer: Je consulte les documents pour répondre à cette question, car elle porte sur la conception du système [source § concept_drift].  Selon le document, pour déclencher un réentraînement en raison de la dérive des données, il faut 3 fenêtres consécutives avec dérive avant que l'action ne soit prise [source § threshold_drift].

### rag-11 — Quelle accuracy le modèle d'origine avait-il sur le jeu de test EuroSAT ?
- tools: []
- missing facts: [['0,978', '0,98', '0.978', '0.98', '97,8', '97.8', '98']] · forbidden: [] · unsupported numbers: []
- answer: Pour répondre à cette question, je vais consulter les documents officiels TerraOps [source § README].


## How to read

- *tool choice* grades the ROUTE: required tools called, no disallowed tool.
- *facts* grades the OUTCOME against ground truth fetched from the API at run time.
- *hallucination* = forbidden phrase, number absent from every tool result, invented citation, or (with a judge) a claim unsupported by the retrieved passages.
- Errors (API down, exceptions) are in errors.jsonl and never counted as wrong answers.
- Ground truth snapshot is in summary.json → meta.ground_truth.
