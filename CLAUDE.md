# TerraOps Copilot — instructions projet

Agent LLM (RAG + tool use) qui pilote la plateforme MLOps TerraOps (`D:\TerraOps`)
via HTTP. **On ne modifie jamais le code de TerraOps.**

## Mode tuteur

- L'utilisateur maîtrise FastAPI/Docker/Python : aller vite dessus. Se concentrer
  sur ce qui est spécifique aux agents LLM (tool use, boucle agentique, RAG, éval).
- Expliquer le concept AVANT de coder ; faire reformuler ; récap + questions
  recruteur à chaque sprint dans `LEARNINGS.md` (français ; code/docs en anglais).

## Invariants de conception

- 6 outils de lecture, 1 outil mutant (`POST /reload`) → confirmation humaine.
- État courant → outil live ; connaissance/concept → `search_documentation` avec
  citations `[source § section]`. Jamais de donnée live dans le corpus RAG.
- Un verdict « inconclusive » reste « inconclusive » (jamais traduit en « no drift »).
- Toute modification de grader/cas → relancer `evaluate.py --agent oracle|null|liar`
  (oracle 100 %, liar 100 % hallucination). Les rapports avant/après un changement de
  grader ne sont pas comparables.
- `/metrics` (texte Prometheus) n'est jamais exposé brut au LLM : parsé et résumé.
- Tout trafic émis par l'agent est tagué `X-TerraOps-Source: agent...`.
- Vérité terrain de l'évaluation = réponses de l'API elle-même.
- **Deux fournisseurs LLM derrière UNE interface** (`agent/provider.py`, Sprint 1) :
  Anthropic (référence, payant — charger le skill `claude-api` avant tout code SDK)
  et Ollama (gratuit, local). L'agent, les outils et l'éval ne dépendent jamais du
  fournisseur ; seul l'adaptateur connaît le format des tool calls. L'éval tourne
  sur les deux et compare (c'est un résultat portfolio en soi).

## Architecture (Sprint 1)

- `llm/types.py` : vocabulaire neutre (messages, ToolSpec, ToolCall, LLMReply).
  `llm/base.py` : interface `LLMClient.chat(system, messages, tools)`.
  Adaptateurs : `anthropic_client.py` (référence), `openai_compat_client.py`
  (LM Studio, Ollama). `factory.py` lit `LLM_PROVIDER` (anthropic | lmstudio).
- `tools/base.py` : `Tool` (nom, description, modèle Pydantic, run, mutating) et
  `ToolRegistry.execute` = SEULE frontière où un ToolCall devient une exécution
  (nom inconnu / args invalides / mutant non confirmé → résultat `is_error`).
- `tools/terraops.py` : 3 outils lecture (`get_api_health`, `get_served_model`,
  `get_registry_champion` via MLflow REST). Les descriptions disent QUAND, QUOI,
  QUAND PAS (outil voisin nommé).
- `agent/loop.py` : boucle ReAct, `max_steps`, appel de clôture sans outils.
  Prompt système : règle 2 = état courant → outils live, concepts → doc ; citations.
- `rag/` (Sprint 2) : `chunking.py` (sections Markdown, 450 car., 2 titres en
  préfixe — MiniLM tronque à 128 tokens), `lexical.py` (BM25 + stopwords FR/EN),
  `store.py` (Chroma persistant `.rag_store/` + `HybridRetriever` RRF),
  `ingest.py` (`python -m terraops_copilot.rag.ingest`, rebuild complet).
  Corpus = snapshot commité `corpus/terraops/` (voir `corpus/MANIFEST.md`) ;
  rien d'exécution-dépendant dedans.
- `tools/docs.py` : `search_documentation` (k ≤ 6, plancher de pertinence,
  ≤ 2 chunks/section, passages cités). `tools/drift.py` : `get_drift_report`
  lance `D:\TerraOps\src\drift_report.py` en sous-processus (seul outil qui
  n'est pas HTTP : pas d'endpoint dérive dans TerraOps) et transmet
  `inconclusive` tel quel.
- `tests/fake_llm.py` : LLM scripté ; la boucle se teste sans réseau ni clé.
- `ui/app.py` (Sprint 4) : chat Streamlit, client léger de l'Agent ; rend les
  événements de `Agent.run(question, on_event=...)` (raison → outil → résultat /
  passages cités → réponse). Port 8502 (8501 = UI carte de TerraOps).
- `Dockerfile` + `docker/entrypoint.sh` + `docker-compose.yml` : `name: terraops`
  + `include:` du compose TerraOps (`${TERRAOPS_REPO:-../TerraOps}`), dépôt
  TerraOps monté RO dans `/terraops` pour `drift_report.py`, volumes `rag-store`
  et `hf-cache`. Image ~3 Go (torch + Evidently) : dette assumée.
- `scripts/record_demo.py` : GIF via Playwright sur la vraie UI. `tests/ui_fake_server.py`
  = UI avec cerveau scripté, TEST ONLY (jamais pour une démo publiée).
- `eval/` (Sprint 3) : `cases.py` (29 cas ; vérité terrain = FONCTION résolue à
  l'exécution contre l'API ; faits = groupes d'alternatives ; `required_tools` ⊂
  `allowed_tools`), `graders.py` (déterministe, atomique : tool_choice, facts,
  citation réelle, refusal, over_refusal, hallucination = phrase interdite / nombre
  non supporté / citation inventée), `judge.py` (LLM-as-a-judge OPTIONNEL,
  fidélité RAG + qualité du refus seulement), `baselines.py` (oracle / null /
  liar pour valider le harnais), `runner.py` (trajectoires, `errors.jsonl`
  séparé, rapport). Entrée : `python evaluate.py` à la racine.

## Commandes

- Stack TerraOps : `cd D:\TerraOps && docker compose up -d` (API prête ~40 s ;
  avant cela `/health` répond par une connexion fermée, pas par un refus).
- Test d'acceptation Sprint 0 : `python scripts/audit_terraops.py` (7/7 attendu).
- Tests : `python -m pytest` (36 tests, sans réseau ni modèle : faux embedder).
- UI : `streamlit run ui/app.py --server.port 8502`. Démo complète :
  `docker compose up` (depuis ce dossier ; TerraOps cloné à côté ou `TERRAOPS_REPO`).
- GIF : `python scripts/record_demo.py` avec l'UI lancée sur un VRAI fournisseur.
- Éval : `python evaluate.py --agent oracle` (harnais), `python evaluate.py --reps 2`
  (vrai agent, provider du `.env`), `--judge` pour le juge, `--only rag,refuse`.
  Rapports dans `eval_reports/<ts>_<label>/report.md` (gitignoré).
- Index RAG : `python -m terraops_copilot.rag.ingest` (243 chunks, ~1 min ; modèle
  d'embedding téléchargé au premier lancement).
- Agent : `python -m terraops_copilot --trace "quel est le modèle champion actuel ?"`
  (`.env` copié depuis `.env.example` ; LM Studio : démarrer le serveur local).

## État

- Sprint 0 (2026-09-09) : audit 7/7 OK, rien à réparer ; squelette créé ;
  mapping endpoint → intention dans `docs/endpoint_audit.md`.
- Décidé : fournisseurs = Anthropic + Ollama ; nom du repo = `terraops-copilot`.
- Sprint 1 (2026-09-09) : interface LLM + 2 adaptateurs, registre d'outils avec
  validation, 3 outils, boucle, CLI, 12 tests verts. Chaîne validée contre le vrai
  TerraOps avec LLM scripté. Test d'acceptation avec vrai LLM : EN ATTENTE (pas de
  clé Anthropic ni serveur LM Studio pendant la session).
- Sprint 2 (2026-09-09) : RAG hybride (Chroma + BM25, RRF) sur snapshot de la doc
  TerraOps, outil `search_documentation`, outil live `get_drift_report`, 22 tests.
  Expérience chunking/embedding documentée dans LEARNINGS.md (troncature 128 tokens,
  e5-small pas mieux, hybride retenu : hit@1 2-3/5, hit@3 3/5 sur 5 questions).
  Routage RAG vs live avec vrai LLM : EN ATTENTE (pas de clé / LM Studio).
- Sprint 3 (2026-09-09) : jeu d'éval de 29 cas, graders déterministes + juge
  optionnel, harnais VALIDÉ (oracle 100/100/100/100/0/0 ; null 0 % faits, 100 %
  refus ; liar 100 % hallucination). Chiffres du VRAI agent : EN ATTENTE (clé /
  LM Studio). Le repo n'est pas encore sous git (à initialiser).
- Sprint 4 (2026-09-09) : UI Streamlit avec raisonnement visible, packaging Docker
  (compose `include`), README narratif + schéma Mermaid, script GIF. 36 tests.
  Build Docker et `docker compose up` : voir ci-dessous. GIF réel : EN ATTENTE
  (fournisseur). README : chiffres du vrai agent à insérer.
- 2026-09-11 : QUATRE RUNS LOCAUX (voir LEARNINGS « Runs 2 à 4 »). Run 4 = Qwen2.5-3B,
  29/29, 0 erreur, 12 min : outil 69 / faits 54 / citation 27 / refus 60 / halluc 17.
  7B : instable (ErrorDeviceLost sur Iris Xe, RAM 16 Go) ; rattrapage des appels en
  texte dans l'adaptateur (live 73 → 90 %) ; prompt v2 (citations inventées 91 → 27 %).
  7 corrections de graders, `--rescore`, coupe-circuit, réponse vide → erreur.
  Modèle local de référence sur cette machine : **qwen2.5-3b-instruct**
  (`lms load qwen2.5-3b-instruct --context-length 8192 --gpu max`, échauffer avant).
  Le conteneur copilot embarque encore le prompt v1 → `docker compose build copilot`.
- 2026-09-11 soir : MESURE DE RÉFÉRENCE Claude Opus 5 (58 lignes, 0 erreur, 10 min,
  ≈ 2,5 $) : outil 97 / faits 94 / citation 100 / refus 90 / halluc 3. Mixed 2/2, piège
  2/2. 4 lignes imparfaites lues (2 rappels RAG, 1 faux positif grader, 1 discutable).
  4 faux positifs de grader supplémentaires trouvés sur les réponses riches de Claude.
  `.env` : LLM_PROVIDER=anthropic, clé présente (jamais dans le chat ni dans git).
- Reste : (1) LM Studio avec GPU offload réduit → `evaluate.py --reps 2` (prompt v2),
  puis Anthropic ; comparer ;
  chiffres dans le README, `record_demo.py` ; (2) `/reload` mutant + confirmation,
  `/predict`, `/metrics` parsé ; (3) passer terraops + terraops-copilot en public.
