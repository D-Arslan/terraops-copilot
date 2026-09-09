# TerraOps Copilot

An LLM agent that operates the [TerraOps](https://github.com/D-Arslan/terraops) MLOps
platform in natural language — RAG over the project's documentation plus tool use over
its HTTP API (serving, monitoring, model registry).

TerraOps itself is untouched: this project only talks to it over HTTP.

## Status

- **Sprint 0 (done)** — audit of the 7 TerraOps endpoints, endpoint → intent mapping,
  project skeleton. See [docs/endpoint_audit.md](docs/endpoint_audit.md).
- **Sprint 1 (done)** — provider interface with two adapters (Anthropic, LM Studio via
  the OpenAI-compatible API), 3 tools with validated arguments, ReAct loop, CLI.
- **Sprint 2 (done)** — hybrid RAG (Chroma embeddings + BM25, reciprocal rank fusion)
  over a committed snapshot of the TerraOps docs, exposed as one more tool with
  citations; live `get_drift_report` tool. The model routes between live tools and
  documentation from the tool descriptions alone.
- **Sprint 3 (done)** — evaluation harness: 29 cases (live / rag / mixed / trap / refuse),
  ground truth resolved at run time from the API itself, deterministic atomic graders
  (tool choice, facts, real citation, refusal, hallucination), optional LLM judge,
  oracle / null / liar control agents. `python evaluate.py`.

## Quick start

```bash
# 1. TerraOps stack must be up (API ready ~40 s after start)
cd D:\TerraOps && docker compose up -d
# 2. Sprint 0 acceptance test
cd D:\terraops-copilot && python scripts/audit_terraops.py
# 3. Configure a provider, then ask
cp .env.example .env   # fill ANTHROPIC_API_KEY, or set LLM_PROVIDER=lmstudio
python -m terraops_copilot.rag.ingest      # build the vector store once (~1 min)
python -m terraops_copilot --trace "quel est le modèle champion actuel ?"   # live tool
python -m terraops_copilot --trace "c'est quoi la dérive ?"                 # RAG, cited
python -m terraops_copilot --trace "y a-t-il de la dérive cette semaine ?"  # live drift
python -m pytest        # loop + tool + RAG + grader tests, no network or model needed
python evaluate.py --agent oracle   # harness self-test (must be ~100 %)
python evaluate.py --reps 2         # evaluate the real agent -> eval_reports/<ts>/report.md
```

## Evaluation

The agent talks to an API whose truth is one HTTP call away, so the eval fetches the
reference answer from the same system at run time and checks the agent against it.
Route and outcome are graded separately; refusals are a graded outcome, not an error;
infrastructure failures go to `errors.jsonl` and are never scored as wrong answers.

Harness validation (no paid model involved):

| control agent | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|
| oracle | 100 | 100 | 100 | 100 | 0 | 0 |
| null ("I don't know") | 17 | 0 | 0 | 100 | 100 | 0 |
| liar (invented numbers) | 17 | 4 | 0 | 0 | 0 | 100 |

Real-agent numbers: run `python evaluate.py --reps 2` with `LLM_PROVIDER=anthropic`, then
with `LLM_PROVIDER=lmstudio`, and compare the two reports.

## Layout

```
src/terraops_copilot/
  llm/      provider-neutral types, LLMClient interface, Anthropic + OpenAI-compat adapters
  client/   HTTP client to TerraOps API + MLflow registry
  tools/    Tool + ToolRegistry (validation boundary), TerraOps / drift / docs tools
  rag/      chunking, BM25 index, Chroma store, hybrid retriever, ingest CLI
  agent/    the ReAct loop
  eval/     cases, graders, judge, baselines, runner
evaluate.py  evaluation entry point
corpus/     committed snapshot of TerraOps documentation (see MANIFEST.md)
  rag/      document ingestion + retrieval
  eval/     question set + API-checked ground truth
scripts/    audit_terraops.py (Sprint 0 acceptance test)
docs/       endpoint_audit.md
LEARNINGS.md  learning journal (French)
```
