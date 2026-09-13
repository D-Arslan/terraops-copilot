# TerraOps Copilot

**An LLM agent that operates an MLOps platform in natural language — and a harness that
measures whether it tells the truth.**

> *"Y a-t-il de la dérive cette semaine ?"* → the agent picks the drift tool, runs the real
> Evidently report against Postgres, and answers *"non concluant : 6 lignes sur 200 requises"*
> instead of *"no drift"*.
> *"C'est quoi la dérive ?"* → it searches the project documentation and answers with a
> citation. Nobody told it which was which.

![demo](docs/demo.gif)

*Recorded on the real UI with Claude Opus 5 by `scripts/record_demo.py` — nothing staged.*

## The problem

[TerraOps](https://github.com/D-Arslan/terraops) is a complete MLOps platform around a
EuroSAT land-use classifier: DVC pipeline, MLflow registry with a promotion gate, FastAPI
serving, Prometheus, Evidently drift monitoring, a continuous-training trigger. Operating it
means knowing seven endpoints, a registry, a CLI and 700 lines of design notes.

The question this project answers: **can an LLM agent sit on top of that platform, choose
by itself between *asking the live system* and *reading the documentation*, and be
trusted?** The last word is the hard one — so the deliverable is not only the agent, it is
the evaluation that puts a number on it.

## Architecture

```mermaid
flowchart LR
    U[User · Streamlit chat] --> A

    subgraph Copilot
        A[Agent loop<br/>think → act → observe]
        R[ToolRegistry<br/>schema validation<br/>human-confirm for mutations]
        L[LLMClient<br/>Anthropic · LM Studio]
        A <--> L
        A --> R
        R --> T1[get_api_health]
        R --> T2[get_served_model]
        R --> T3[get_registry_champion]
        R --> T4[get_drift_report]
        R --> T5[search_documentation]
        T5 --> H[Hybrid retrieval<br/>Chroma embeddings + BM25 · RRF]
        H --> C[(corpus<br/>committed snapshot<br/>of TerraOps docs)]
    end

    subgraph TerraOps  [TerraOps — untouched]
        T1 & T2 --> API[FastAPI :8000]
        T3 --> ML[MLflow registry :5000]
        T4 --> DR[drift_report.py<br/>Evidently over Postgres]
    end

    subgraph Eval
        E[evaluate.py<br/>29 cases · ground truth fetched<br/>from the API at run time] -.-> A
        E -.-> API
        E -.-> ML
    end
```

Two design lines run through everything:

- **State vs knowledge.** Anything that changes at runtime (served version, drift verdict,
  counters) comes from a live tool; anything written (what drift is, gate thresholds, known
  limits) comes from a committed documentation snapshot through RAG. The model routes
  between them from the tool descriptions alone — that routing is what the eval measures.
- **The model plans, the code executes.** A tool call is untrusted input: unknown tool,
  invalid arguments (Pydantic), or a mutating action without human confirmation are refused
  before anything touches TerraOps. Errors go back to the model as observations, never as
  crashes.

## Evaluation — the differentiator

The agent talks to an API whose truth is one HTTP call away. So the eval fetches the
reference answer from the same system **at run time** and checks the agent against it.

| category | n | ground truth | graded |
|---|---|---|---|
| live | 11 | API / registry / drift CLI, called directly | required tool, facts, unsupported numbers |
| rag | 11 | terms known to be in the corpus | docs tool, facts, **citation that the tool really returned** |
| mixed | 1 | two live calls compared | both tools, verdict |
| trap | 1 | false premise ("why is v3 the champion?") | correction with live data |
| refuse | 5 | no tool can answer | refusal marker, zero invented number, no claimed action |

Route (tool choice) and outcome (facts) are graded separately. Hallucination is
deterministic where it can be: forbidden phrase, number absent from every tool result,
citation the tool never returned. An optional LLM judge covers only what code cannot see
(faithfulness to retrieved passages, refusal quality). Infrastructure failures go to
`errors.jsonl` and are never scored as wrong answers.

**Harness validation** — before spending on a model, three control brains run through the
same loop and the same tools:

| control agent | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|
| oracle (perfect route & facts) | 100 | 100 | 100 | 100 | 0 | 0 |
| null ("I don't know") | 17 | 0 | 0 | 100 | 100 | 0 |
| liar (invented numbers) | 17 | 4 | 0 | 0 | 0 | 100 |

The liar caught two graders that were too lenient (`1` matching inside `1234`, *chargé*
matching inside *rechargé*) before any real number was produced. The three controls were
re-run on 2026-09-13 with the current graders; reports in [docs/eval/](docs/eval/).

**Real agent — reference vs local.** Same 29 cases, same deterministic graders, every
run re-scored with the current grader version (`python evaluate.py --rescore <dir>`).
Reports, original and rescored, are versioned in [docs/eval/](docs/eval/):

| model | rows | tool choice | facts | citation | refusal | over-refusal | halluc. | s/question | cost |
|---|---|---|---|---|---|---|---|---|---|
| **Claude Opus 5** (Anthropic), rescored | 58 (2 reps) | **97** | **94** | **100** | **90** | 4 | **3** | 10 | $2.46 |
| Qwen2.5-3B (LM Studio, local), rescored | 29 | 69 | 54 | 27 | 60 | 4 | 17 | 46 | 0 |
| Qwen2.5-coder-7B (local, best partial run) | 10 | 90 | 80 | — | — | 0 | 10 | 60 | 0 |

*Rescored* means graded again with the graders at commit `21128ae`, after eleven fixes
made while reading the answers; the original reports scored Claude at 50 refusal /
15.5 hallucination and the 3B at 40 / 24.1 (`summary.json` vs `summary.rescored.json`).
Cost is the list price of 336 896 input and 30 925 output tokens from the report,
prompt caching not accounted.

Per category, Claude: live 100 % tool / 95 % facts; rag 100 % tool / 91 % facts / 100 %
real citations; the two-tool question 2/2 (no local model managed it); the false-premise
trap 2/2; refusals 9/10. Its four imperfect rows out of 58 are two retrieval misses
answered cautiously with real citations, one string-grader false positive (it wrote
*"ce n'est donc pas « pas de dérive »"*), and one debatable "closest approximation" on a
refuse case.

What the local runs found before that: with prompt v1, the 7B cited a passage the tool
had actually returned in 2 of 22 rag answers and invented a `[source § …]` citation in
12 of them, copying the prompt's placeholder (prompt v2: a concrete example, no citation
without the tool; 3 of 11 invented afterwards, still 2 real); it then wrote tool calls
as text after its "why" sentence and the OpenAI-compatible server dropped them (the
adapter now salvages `[tool] {json} [END_TOOL_REQUEST]`, live routing 73 → 90 %); the
laptop's integrated GPU died under sustained load (errors quarantined, circuit breaker
added); the 3B is three times faster, finishes cleanly and actually uses the
documentation tool. Across all runs: local models do not hallucinate live facts, but
invent on *refuse* questions and fall for the false premise. About one KO row in three
was a grader defect, not a model one; eleven grader fixes came out of reading them
(seven from the local runs, four from Claude's) - several only surfaced on Claude's
richer answers, which a grader calibrated on small models under-scored (15 % → 3 %
hallucination after fixing timestamps, "24 h", *"impossible à savoir"*).

Noise floor: 29 cases × 2 reps ≈ ±13 points on a rate; the Claude-vs-local gaps are far
above it, differences between local runs mostly are not.

## Run the demo

```bash
git clone https://github.com/D-Arslan/terraops.git          # sibling checkout
git clone https://github.com/D-Arslan/terraops-copilot.git
cd terraops-copilot
cp .env.example .env         # ANTHROPIC_API_KEY=…  or  LLM_PROVIDER=lmstudio (LM Studio on the host)
docker compose up            # TerraOps stack + copilot; UI on http://localhost:8502
```

First boot downloads the embedding model and builds the vector store (kept in volumes).
The compose file *includes* TerraOps' own compose unchanged and mounts its repo read-only.

Local development:

```bash
pip install -e . && pip install pytest
python -m terraops_copilot.rag.ingest                       # vector store
python -m terraops_copilot --trace "quel est le modèle champion actuel ?"
streamlit run ui/app.py --server.port 8502                  # the chat UI
python -m pytest                                            # 44 tests, no network, no model
python evaluate.py --agent oracle                           # harness self-test
python scripts/record_demo.py                               # regenerate docs/demo.gif
```

## What I learned (and would say in an interview)

- A chatbot says; an agent acts and observes. The whole difficulty moves into three
  places: the tool descriptions (they *are* the prompt), the validation boundary, and the
  evaluation.
- Small embedding models truncate silently — 106 of my first 120 chunks were cut at 128
  tokens. Hybrid retrieval (BM25 + embeddings) beat a bigger embedding model on this
  bilingual, identifier-heavy corpus.
- "Not enough data" must survive the trip through the agent. A tool result of
  *inconclusive* that comes out as *no drift* is the most dangerous failure in the set,
  and it is the one the eval checks first.
- Evaluating an agent is harder than evaluating a classifier: several valid routes, several
  valid phrasings, and "I cannot" as a correct answer. Ground truth has to be a function,
  not a constant.

Full journal (French): [LEARNINGS.md](LEARNINGS.md). Endpoint audit: [docs/endpoint_audit.md](docs/endpoint_audit.md).

## Layout

```
src/terraops_copilot/
  llm/      provider-neutral types, LLMClient, Anthropic + OpenAI-compatible adapters
  client/   HTTP client to the TerraOps API + MLflow registry
  tools/    Tool + ToolRegistry (validation boundary); TerraOps, drift, docs tools
  rag/      chunking, BM25, Chroma store, hybrid retriever, ingest CLI
  agent/    the ReAct loop (emits events for the UI)
  eval/     cases, graders, judge, control agents, runner
ui/app.py       Streamlit chat showing the agent's reasoning and sources
evaluate.py     evaluation entry point
corpus/         committed snapshot of TerraOps documentation
docker/, Dockerfile, docker-compose.yml   one-command demo
```

## Limits, stated

- The drift tool runs TerraOps' `drift_report.py` as a subprocess (there is no drift
  endpoint on that side yet), which is why the image carries torch and Evidently.
- 29 cases × 2 reps gives roughly ±13 points on a rate: enough to tell good from bad, not to
  rank two close prompts. More reps or more cases before any prompt hill-climbing.
- The LLM judge is not calibrated against human labels yet; its verdicts are reported, not
  trusted blindly.
- Five of the seven TerraOps endpoints (`/predict`, `/predict/batch`, `/metrics`,
  `/monitoring/status`, `/reload`) are not exposed as tools yet; `/reload` will be the
  first mutating tool, behind a human confirmation.
