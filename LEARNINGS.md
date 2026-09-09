# LEARNINGS — TerraOps Copilot

Journal d'apprentissage (français). Un sprint = une section : concept, décisions,
ce qui a cassé, questions recruteur. Le code et les docs projet sont en anglais.

---

## Sprint 0 — Audit & socle (2026-09-09)

### Concept 1 : chatbot vs agent

- **Chatbot** : `texte → LLM → texte`. Le modèle ne peut que *dire*. S'il affirme
  « le modèle servi est la v1 », c'est une hallucination plausible, pas une lecture.
- **Agent** : `texte → LLM → (appel d'outil → résultat)* → texte`. Le modèle peut
  *agir* sur le monde et *observer* le résultat avant de répondre. La boucle
  (« agentic loop ») est le cœur : le LLM produit une *demande d'appel*, MON code
  exécute réellement l'appel HTTP, renvoie le résultat au LLM, qui décide de
  continuer ou de conclure.
- Pourquoi le tool use est le sujet : sans lui, « quelle version est servie ? »
  n'a pas de réponse fiable. Avec lui, la réponse vient de `GET /model-info`, donc
  elle est vérifiable — et c'est exactement ce qui rend le jeu d'évaluation possible.
- Point subtil : le LLM n'exécute JAMAIS rien. Il émet un JSON structuré
  `{name, arguments}`. L'exécution, la validation, les timeouts, la confirmation
  humaine : c'est mon code. Le LLM est un *planificateur*, pas un *exécuteur*.

### Concept 2 : un outil vu par le LLM

- Un outil = **nom + description + schéma JSON des paramètres**. Le modèle ne voit
  ni le code, ni l'URL : seulement cette carte de visite, injectée dans le prompt.
- Comment il « décide » : le modèle est entraîné (fine-tuning) à émettre un bloc
  d'appel d'outil quand la requête est mieux servie par un outil. Techniquement,
  c'est de la génération de tokens conditionnée par les descriptions. Donc :
  **la description est du prompt engineering**. Une description floue = mauvais
  choix d'outil ou mauvais arguments. Deux outils aux descriptions proches
  (`/health` vs `/monitoring/status`) → il faut expliciter la frontière dans le texte.
- Le schéma JSON (JSON Schema) contraint les arguments : types, `enum`, `required`.
  Bonne pratique : `description` sur CHAQUE paramètre, et exemples dans la
  description de l'outil.
- Découverte du jour : TerraOps expose `GET /openapi.json`. Le schéma OpenAPI est
  déjà un JSON Schema par endpoint → les descriptions d'outils peuvent être
  **dérivées** de l'API plutôt que recopiées. Piste Sprint 1 (à trancher : dérivé
  automatiquement = toujours à jour mais descriptions pauvres ; écrit à la main =
  meilleure sémantique mais dérive possible).

### Audit TerraOps

- `docker compose up -d` → 6 conteneurs, API prête ~40 s après le démarrage.
- **7/7 endpoints OK**, rien à réparer. Détail dans `docs/endpoint_audit.md`.
- Piège vu en vrai : `RemoteDisconnected` sur `/health` pendant les 40 premières
  secondes. Le port est publié avant que uvicorn n'écoute. Le client de l'agent
  devra faire une attente/retry sur ce cas précis.
- `/monitoring/status` disait `rows_written=0` juste après 3 prédictions, puis 3
  quelques secondes après : le log est asynchrone (file + thread). Un outil qui lit
  ce compteur juste après un predict peut « mentir » — à documenter dans la
  description de l'outil.

### Décisions de socle

- Projet séparé `D:\terraops-copilot`, ne touche jamais au code de TerraOps :
  uniquement HTTP vers `localhost:8000` (+ plus tard MLflow `:5000`, Prometheus `:9090`).
- Classement des 7 outils : 6 lectures sûres, **1 mutation** (`/reload`) qui exige
  une confirmation humaine. Cette asymétrie est une propriété de conception de
  l'agent, pas un détail.
- `/metrics` ne sera pas exposé brut au LLM : outil qui parse et résume.
- Ce que l'API ne sait pas répondre (pourquoi un refus du gate, seuils, dérive
  hebdo) délimite le périmètre RAG + outils MLflow des sprints suivants.

### Décision fournisseur (fin Sprint 0)

- **Les deux** : Anthropic (payant, référence) + Ollama (gratuit, local).
- Conséquence architecturale : une interface `LLMProvider` unique
  (`(messages, tools) → texte | liste de tool calls`) et deux adaptateurs. Le
  reste du code (outils, boucle, RAG, éval) ne sait pas quel modèle tourne.
- Pourquoi c'est un vrai sujet et pas de la plomberie : les deux fournisseurs
  ne parlent PAS le même dialecte de tool use (blocs `tool_use`/`tool_result`
  chez Anthropic, `tool_calls` de style OpenAI chez Ollama ; les modèles locaux
  respectent moins bien les schémas). L'adaptateur absorbe ça. Et l'éval qui
  tourne sur les deux donne un chiffre comparable : « X % de bonnes réponses
  avec Claude vs Y % avec un 8B local » — un résultat de portfolio.
- Ordre : Anthropic d'abord (function calling fiable = on valide la boucle),
  Ollama ensuite (on mesure ce qui se dégrade).

### Questions recruteur (Sprint 0)

1. Quelle est la différence entre un chatbot et un agent ? Où est la boucle ?
2. Qui exécute un appel d'outil : le modèle ou votre code ? Pourquoi ça compte
   pour la sécurité ?
3. Comment décrivez-vous un outil au modèle ? Que se passe-t-il si deux outils ont
   des descriptions ambiguës ?
4. Pourquoi ne pas donner directement `openapi.json` au modèle comme liste d'outils ?
5. Comment traitez-vous un outil qui modifie l'état du système (`/reload`) différemment
   d'une lecture ?
6. Comment savez-vous que votre agent répond juste ? (→ la vérité terrain vient de
   l'API elle-même, d'où le jeu d'évaluation.)
7. Pourquoi une abstraction fournisseur ? Qu'est-ce qui diffère concrètement entre
   le tool use d'Anthropic et celui d'un modèle local ?

### Ma compréhension à valider (à reformuler par moi avant Sprint 1)

- [ ] Le LLM ne fait qu'émettre un JSON `{name, arguments}` ; mon code exécute.
- [ ] La description d'un outil est du prompt : elle pilote le choix du modèle.
- [ ] Un agent sans évaluation, c'est un chatbot avec des effets de bord.

---

## Sprint 1 — Le cœur agentique (2026-09-09)

### Concept 3 : le cycle ReAct (raisonner → agir → observer → recommencer)

- Un appel unique ne suffit pas parce que le modèle **ne connaît pas le résultat
  avant de l'avoir observé**. « Quel est le champion ? » : à l'appel 1, le modèle
  ne peut qu'émettre une demande d'outil. La réponse en langage naturel n'est
  possible qu'à l'appel 2, une fois le résultat injecté dans l'historique.
- Chaque tour est une requête HTTP **complète et sans état** : on renvoie toute la
  conversation. La « mémoire » de l'agent, c'est la liste de messages que notre
  boucle fait grossir (`agent/loop.py`). Le modèle ne se souvient que de ce qu'on
  lui remet.
- Quand une question exige deux outils qui dépendent l'un de l'autre (« le
  champion du registry est-il bien celui qui est servi ? »), il faut 3 tours.
  D'où l'itération. Et d'où le garde-fou `max_steps` : un modèle qui boucle
  coûterait de l'argent sans fin. Le test `test_max_steps_stops_a_runaway_model`
  a attrapé un vrai bug : à l'appel de clôture je faisais confiance au modèle pour
  ne plus demander d'outil. Le garde-fou est maintenant dans la boucle.

### Concept 4 : la description d'un outil décide de son usage

- **Mauvaise** : `get_model_info — Returns model info.` Le modèle ne sait pas
  quand l'appeler, ni ce qu'il recevra, ni comment le distinguer de
  `get_registry_champion`. Il choisira au hasard ou n'appellera rien.
- **Bonne** (celle du code) : « Describe the model CURRENTLY LOADED in the serving
  API … Use for 'which model is serving right now?' … This is the live API view;
  it can lag behind the registry if a new champion was promoted but the API was
  not reloaded — compare with get_registry_champion for that. »
  Elle dit QUAND (intentions utilisateur citées), QUOI (champs retournés), et
  QUAND PAS (l'outil voisin, nommé). Trois outils, trois frontières explicites.
- Hygiène de schéma vue en vrai : Pydantic injecte `title` et la docstring de la
  classe dans le JSON Schema. Pour le modèle c'est du bruit (tokens), et ça peut
  contredire la description. `Tool.spec()` les retire.
- `Literal["champion"]` → `const` dans le schéma : le modèle ne peut pas inventer
  un alias. Quand il le fait quand même (`challenger`), la validation le refuse et
  le message d'erreur Pydantic lui est renvoyé pour qu'il se corrige.

### Concept 5 : sécurité — le LLM est une entrée non fiable

- Tout ce que le modèle produit (nom d'outil, arguments) est une **entrée
  utilisateur indirecte** : influencée par la question, par les résultats d'outils
  précédents (injection via une doc ou une réponse d'API), et par le hasard du
  sampling. On valide donc TOUJOURS avant d'exécuter, dans `ToolRegistry.execute` :
  1. nom inconnu → refus, rien ne tourne ;
  2. arguments hors schéma (type, champ en trop, valeur hors `const`) → refus ;
  3. outil mutant → confirmation humaine ou refus (aucun mutant dans ce sprint,
     le mécanisme est en place pour `/reload`).
- Les refus repartent au modèle comme observations `is_error`, pas comme
  exceptions : la boucle ne plante pas, le modèle s'explique ou se corrige.
- Les exceptions réseau (503, timeout) suivent le même chemin. Un agent qui plante
  sur un 503 n'est pas un agent d'exploitation.

### Deux fournisseurs, une interface

- `llm/types.py` : vocabulaire neutre (`UserMessage`, `AssistantMessage` avec
  `tool_calls`, `ToolResultMessage`, `ToolSpec`, `LLMReply`). L'agent, les outils,
  les tests ne voient que ça.
- `AnthropicClient` : outils en `input_schema`, demandes en blocs `tool_use`,
  observations en blocs `tool_result` dans un message **user** (groupés en un seul
  message si plusieurs), `stop_reason == "tool_use"`.
- `OpenAICompatClient` (LM Studio) : outils enveloppés `{"type":"function"}`,
  demandes en `message.tool_calls` avec `arguments` en **chaîne JSON** (à parser,
  parfois cassée sur les petits modèles), observations en messages `role: tool`.
- `FakeLLM` (tests) : 3e implémentation, scriptée. Preuve que la boucle ne dépend
  d'aucun fournisseur — c'est ce que réutilisera l'évaluation.

### État du test d'acceptation

- Chaîne validée bout en bout avec LLM scripté contre le VRAI TerraOps :
  `get_registry_champion` → `{"version": "1", "tags": {"gate_accuracy": "0.9810",
  "gate_result": "promoted", …}}`, `get_served_model` → v1, 10 classes, cpu.
- Reste à exécuter avec un vrai modèle : ni clé Anthropic ni serveur LM Studio
  démarré pendant la session. Commande :
  `python -m terraops_copilot --trace "quel est le modèle champion actuel ?"`

### Questions recruteur (Sprint 1)

1. Décrivez le cycle d'un agent tool-use. Pourquoi plusieurs appels au modèle ?
2. Où vit la mémoire d'un agent ? Que se passe-t-il si vous perdez la liste de
   messages entre deux tours ?
3. Donnez une mauvaise et une bonne description d'outil. Qu'est-ce qui change
   dans le comportement du modèle ?
4. Pourquoi valider des arguments produits par le modèle alors qu'on lui a donné
   le schéma ? (indice : le schéma est une suggestion, la validation une garantie)
5. Que renvoyez-vous au modèle quand un outil échoue, et pourquoi pas une exception ?
6. Comment empêchez-vous un agent de boucler indéfiniment ?
7. Quelles différences concrètes entre le tool use d'Anthropic et le dialecte
   OpenAI utilisé par LM Studio ? Comment votre code les isole-t-il ?

### Ma compréhension à valider (à reformuler avant Sprint 2)

- [ ] Pourquoi « quel est le champion ? » coûte 2 appels LLM minimum.
- [ ] Ce qui, dans une description d'outil, fait la différence entre appel correct
      et appel raté.
- [ ] Pourquoi la validation Pydantic est une frontière de sécurité et pas du
      confort de typage.

---

## Sprint 2 — RAG hybride : la question choisit l'outil (2026-09-09)

### Concept 6 : la frontière RAG vs tool

- **Le RAG répond à « qu'est-ce que / pourquoi / comment ça marche »**. C'est de la
  connaissance ÉCRITE, stable entre deux commits. On l'indexe une fois, on la
  cite.
- **Un tool répond à « maintenant / cette semaine / combien / lequel »**. C'est
  de l'ÉTAT, périmé dès qu'il est produit. Le mettre dans le RAG, c'est servir
  une valeur d'hier avec l'assurance d'une doc : la version servie, le verdict de
  dérive, les compteurs. Un index est une photo ; l'API est le direct.
- Symétriquement, mettre la doc conceptuelle dans une API n'a aucun sens : il
  n'y a rien à calculer, et une API ne cite pas ses sources.
- Le corpus (`corpus/MANIFEST.md`) est donc un **snapshot commité** (commit
  `7fda55f` de TerraOps) : reproductible, versionné avec l'agent, et il ne
  contient volontairement rien qui change à l'exécution.
- Dans ce projet, la frontière est aussi matérialisée par le prompt système
  (règle 2) et par les descriptions croisées : chaque outil nomme son voisin et
  dit « pas pour ça ». Ce n'est pas moi qui route : c'est le modèle, à partir de
  ces textes. Le test d'acceptation vérifie précisément ce routage.

### Concept 7 : embedding ≠ mots-clés — et pourquoi il faut les deux

- Un embedding est un vecteur (384 dimensions ici) tel que deux textes de SENS
  proche ont des vecteurs proches (cosinus). « promotion d'un modèle » et « gate
  champion/challenger » ne partagent aucun mot mais sont voisins.
- Limite mesurée : un petit modèle bilingue floute les IDENTIFIANTS.
  `min_delta`, `Wasserstein`, `X-TerraOps-Source` sont des chaînes exactes que
  BM25 (fréquence de termes, IDF) retrouve à coup sûr et que l'embedding rate.
- D'où l'**hybride** : dense (Chroma) + lexical (BM25) fusionnés par *reciprocal
  rank fusion* (score = Σ 1/(60+rang)). Basé sur les rangs, donc pas besoin de
  calibrer deux échelles incomparables (cosinus vs BM25).
- Détail qui compte : sans **stopwords** FR/EN, « c'est quoi la dérive ? »
  matchait tout le corpus sur « la » et « est ». Avec, la requête se réduit à
  `derive` (accents retirés).

### Expérience : ce qui a vraiment amélioré le retrieval

Étalon : 5 questions, section attendue connue. Mesure hit@1 / hit@3.

| Config | hit@1 | hit@3 | Leçon |
|---|---|---|---|
| MiniLM, chunks 1200 car., chemin complet de titres | 0/5 | 3/5 | **106 chunks sur 120 tronqués** : MiniLM n'embarque que 128 tokens, mes chunks en faisaient 271 en médiane. Un seul warning, facile à rater. |
| MiniLM, 600 car., chemin complet | 0/5 | 0/5 | Le préfixe de titres mangeait un tiers de la fenêtre. |
| MiniLM, 450 car., 2 titres | 1/5 | 3/5 | Mieux, mais le modèle reste faible sur ce corpus. |
| multilingual-e5-small (512 tokens), 450–1200 | 0–1/5 | 2–3/5 | Pas mieux, et scores non discriminants (« pizza » à 0,83). Plus gros ≠ meilleur. |
| BM25 seul | 2/5 | 3/5 | Les identifiants exacts. |
| **Hybride RRF (retenu)** | **2–3/5** | **3/5** | Complémentaires. |

- Le point non mesuré par cet étalon : **c'est le LLM qui écrit la requête**.
  Sur « c'est quoi la dérive ? » brut, le top-1 est une section de questions
  recruteur qui définit aussi la dérive. Quand le modèle reformule en « qu'est-ce
  que la dérive (data drift) », les 4 passages viennent de « Concept n°1 — Data
  drift vs concept drift ». La description de l'outil guide cette reformulation.
- Mon étalon est strict (une seule section « attendue » alors que 3 en parlent).
  À transformer en vrai jeu d'évaluation au Sprint 3, avec plusieurs sections
  acceptables et un juge.

### Concept 8 : over-retrieval

- Injecter 10 passages « au cas où » dégrade la réponse : plus de tokens (coût,
  latence), plus de distracteurs (le modèle cite le mauvais), et l'effet
  « lost in the middle » (les passages du milieu sont moins utilisés).
- Garde-fous côté code, pas côté modèle : `k` par défaut 4, max 6 (validé par le
  schéma) ; plancher de pertinence (cosinus ≥ 0,25 OU au moins un terme de la
  requête présent) ; au plus 2 chunks par section (les fenêtres qui se
  chevauchent sont des quasi-doublons) ; résultat vide explicite → le modèle
  doit dire « la doc ne couvre pas ». « recette de pizza » → 0 passage.

### L'outil de dérive live

- TerraOps n'a pas d'endpoint HTTP pour la dérive (dette connue). L'outil
  `get_drift_report` lance `src/drift_report.py` en sous-processus (appelé, pas
  modifié), sort les rapports dans un dossier temporaire, lit le JSON.
- Il transmet l'`insufficient_data` tel quel : cette semaine, 6 lignes pour 200
  requises → verdict « inconclusive ». Un agent qui traduit « pas assez de
  données » en « pas de dérive » est pire que pas d'agent. Test unitaire dédié.

### État du test d'acceptation

- Mécanique validée avec LLM scripté contre le vrai store et le vrai TerraOps :
  Q1 → `search_documentation` → 4 passages cités « Concept n°1 — Data drift vs
  concept drift » ; Q2 → `get_drift_report` → inconclusive, 6/200 lignes.
- Le ROUTAGE (le modèle choisit seul) reste à observer avec un vrai LLM :
  `python -m terraops_copilot --trace "c'est quoi la dérive ?"` puis
  `python -m terraops_copilot --trace "y a-t-il de la dérive cette semaine ?"`.

### Questions recruteur (Sprint 2)

1. Pourquoi ne met-on pas les métriques live dans le RAG ? Et la doc dans une API ?
2. Qu'est-ce qu'un embedding ? Donnez un cas où la recherche sémantique bat les
   mots-clés, et un cas inverse.
3. Comment fusionnez-vous deux retrievers dont les scores ne sont pas comparables ?
4. Vous aviez 106 chunks sur 120 tronqués sans erreur. Comment l'avez-vous
   découvert, et quelle règle en tirez-vous pour choisir une taille de chunk ?
5. Qu'est-ce que l'over-retrieval et quels garde-fous avez-vous mis ?
6. Comment l'agent décide-t-il entre RAG et appel d'API ? Où est ce « routage » ?
7. Comment garantissez-vous que chaque réponse RAG cite ses sources ?
8. Que fait votre agent quand le monitoring dit « pas assez de données » ?

### Ma compréhension à valider (à reformuler avant Sprint 3)

- [ ] La règle « état → tool, connaissance → RAG », avec un exemple de chaque
      côté et un exemple mixte.
- [ ] Pourquoi BM25 et embeddings sont complémentaires sur CE corpus.
- [ ] Ce que la troncature à 128 tokens a fait à mes premiers résultats.

---

## Sprint 3 — Le jeu d'évaluation (2026-09-09)

### Concept 9 : pourquoi évaluer un agent est plus dur qu'évaluer un classifieur

- Un classifieur : une entrée, une étiquette, une métrique (accuracy). La vérité
  terrain est une valeur, la comparaison est une égalité.
- Un agent : une question, PLUSIEURS chemins valides (appeler `get_served_model`
  ou `get_api_health` donnent tous deux la version servie), PLUSIEURS formulations
  valides (« v1 », « version 1 », « 98,1 % », « 0.981 »), et des réponses qui n'ont
  pas de valeur de référence (« je ne peux pas » est la bonne réponse à cinq
  questions du jeu). En plus, l'agent est stochastique : deux exécutions de la même
  question peuvent prendre des routes différentes.
- Conséquences dans le code : (1) la vérité terrain est une FONCTION résolue à
  l'exécution contre l'API, pas une constante (`cases.py`) ; (2) chaque fait est
  une liste d'alternatives équivalentes, normalisées (accents, casse, virgule
  décimale, pourcentage) ; (3) `required_tools` ⊂ `allowed_tools` plutôt qu'une
  séquence exacte ; (4) l'option `--reps` pour mesurer la variance.

### Concept 10 : évaluer le résultat ≠ évaluer la route

- **Résultat** (`facts`) : la réponse contient-elle la vérité ? C'est ce que
  l'utilisateur voit.
- **Route** (`tool_choice`) : l'agent a-t-il appelé les outils requis et aucun
  outil interdit ? C'est ce que ce projet teste vraiment (RAG vs live). Une bonne
  réponse par la mauvaise route est un coup de chance, pas une capacité — et la
  chance ne se reproduit pas en production.
- Les deux sont des colonnes SÉPARÉES du rapport, jamais fusionnées en un score.
  Idem pour `citation`, `refusal`, `over_refusal`, `hallucination` : des vérifications
  atomiques, chacune diagnostique une chose.
- Nuance apprise de la checklist d'éval : grader la route est un choix assumé ici
  parce que la question du sprint EST le routage. Sur un agent de production on
  graderait plutôt l'état final.

### Concept 11 : LLM-as-a-judge, et ses limites

- Un juge LLM lit (question, preuves, réponse candidate) et rend un verdict
  structuré. Ici il ne sert QUE là où le déterminisme ne voit pas : (a) la
  fidélité d'une réponse RAG aux passages retournés (une phrase plausible mais
  absente des passages) ; (b) la qualité d'un refus (décline clairement, n'invente
  ni fait ni action).
- Tout le reste reste déterministe (outil, faits, citations, nombres non supportés) :
  moins cher, reproductible, sans biais.
- Limites, et ce que le code fait contre : biais de longueur (consigne explicite),
  auto-préférence (juge configurable dans une autre famille via `JUDGE_PROVIDER` /
  `JUDGE_MODEL`, usage comptabilisé à part), injection (le candidat est passé entre
  délimiteurs comme DONNÉE, jamais comme instruction), non-déterminisme (à mesurer
  en rejouant le juge), et surtout **absence de calibration** : un juge non comparé
  à des étiquettes humaines est une opinion. À faire : étiqueter à la main ~30
  réponses et rapporter l'accord.

### Le jeu : 29 cas

| Catégorie | n | Vérité terrain | Ce qui est gradé |
|---|---|---|---|
| live | 11 | appel direct à l'API/registry/CLI dérive | outil requis, faits, nombres non supportés |
| rag | 11 | termes connus du corpus (params.yaml, learning.md) | outil doc, faits, **citation réelle** |
| mixed | 1 | deux appels comparés | les deux outils, verdict |
| trap | 1 | fausse prémisse (« pourquoi le champion est la v3 ? ») | la correction (v1) et pas de confirmation |
| refuse | 5 | aucun outil ne peut répondre | marqueur de refus, zéro nombre inventé, pas d'action prétendue |

- Détecteurs d'hallucination déterministes : phrase interdite (« pas de dérive »
  quand le verdict est « inconclusive »), nombre absent de tous les résultats
  d'outils et de la question, **citation qui n'a pas été retournée par l'outil**.
- `errors.jsonl` : une API tombée ou une exception n'est JAMAIS comptée comme une
  mauvaise réponse (« pas de réponse » ≠ « réponse fausse »).

### Validation du harnais avant le premier centime

| Agent de contrôle | outil | faits | citation | refus | sur-refus | hallucination |
|---|---|---|---|---|---|---|
| oracle (route et faits parfaits) | 100 | 100 | 100 | 100 | 0 | 0 |
| null (« je ne sais pas ») | 17 | 0 | 0 | 100 | 100 | 0 |
| liar (nombres inventés, sans outil) | 17 | 4 | 0 | 0 | 0 | 100 |

- Le 17 % d'« outil » des baselines = les 5 cas de refus où ne rien appeler est
  correct. Le 4 % de faits du menteur = 1 cas (rag-02 : « champion » et « gate » sont
  des mots génériques) : connu, et c'est la colonne hallucination qui le rattrape (100 %).
- Deux bugs attrapés par cette validation : l'alternative « 1 » matchait dans
  « 1234 », et « chargé » matchait dans « rechargé ». Les faits exigent maintenant
  des frontières de mot (menteur : 29 % → 8 % → 4 % de faits). Sans l'agent
  menteur, ce grader trop laxiste aurait gonflé le score du vrai agent.

### Ce que je peux dire en entretien (et ce que je ne peux pas encore)

- « Mon harnais est validé : un oracle fait 100 %, un menteur est détecté à 100 %. »
- « Les chiffres du vrai agent » : PAS ENCORE MESURÉS (ni clé Anthropic ni serveur
  LM Studio pendant la session). Commande : `python evaluate.py --reps 2` puis
  `LLM_PROVIDER=lmstudio python evaluate.py --reps 2` ; comparer les deux rapports.
- Marge d'erreur attendue : 29 cas × 2 reps ≈ ±13 points sur un taux. Assez pour
  voir « bon / mauvais », pas pour départager deux prompts proches → plus de reps
  ou plus de cas avant tout hill-climbing.

### Questions recruteur (Sprint 3)

1. Pourquoi la vérité terrain est-elle calculée à l'exécution et pas stockée ?
2. Différence entre gradez le résultat et gradez la route ; quand faut-il l'un, l'autre ?
3. Comment détectez-vous une hallucination sans juge LLM ? Citez trois détecteurs.
4. Comment avez-vous validé que votre harnais mesure quelque chose ? (oracle / null / liar)
5. Quelles limites du LLM-as-a-judge, et lesquelles votre code atténue ?
6. Un agent qui refuse tout a 100 % de refus correct : quelle métrique l'empêche de gagner ?
7. Avec 29 cas, quelle est votre marge d'erreur, et que faites-vous d'une différence
   de 5 points entre deux prompts ?
8. Que se passe-t-il dans votre rapport quand TerraOps est éteint pendant l'éval ?

### Ma compréhension à valider (à reformuler)

- [ ] Pourquoi « plusieurs chemins valides » change la façon d'écrire la vérité terrain.
- [ ] Ce qu'un oracle et un menteur prouvent chacun sur le harnais.
- [ ] Pourquoi le juge ne grade que la fidélité et le refus, et pas les faits.
