# Design notes

What the README states, with the reasoning, the measurements and the caveats behind each
point. Numbers come from the versioned reports in [eval/](eval/).

## 1. State vs knowledge: the routing rule

A tool answers *now / this week / how many / which one*: state, stale the moment it is
produced (served version, drift verdict, counters). Retrieval answers *what is / why / how
does it work*: written knowledge, stable between two commits, citable. Putting state in the
index would serve yesterday's value with the confidence of a document; putting concepts
behind an API would give nothing to compute and no source to cite.

Nothing in the code routes. The system prompt states the rule, each tool description names
its neighbour and says what it is *not* for (`get_served_model` is the live API view and
"can lag behind the registry if a new champion was promoted but the API was not reloaded;
compare with `get_registry_champion` for that"), and the model decides. The evaluation's
`tool_choice` column measures exactly that decision: Claude 97 %, Qwen2.5-3B 69 %,
Qwen2.5-coder-7B with the first prompt 56 % (it answered documentation questions from
memory, calling the docs tool 3 times out of 22).

The corpus is a committed snapshot of TerraOps' documentation ([../corpus/MANIFEST.md](../corpus/MANIFEST.md)),
with nothing that changes at runtime in it. Reproducible retrieval, versioned with the agent,
and a known debt: it lags the platform's docs.

## 2. The model plans, the code executes

Everything the model emits, tool name and arguments, is indirect user input: shaped by the
question, by earlier tool results (a document or an API answer can carry an injection), and by
sampling. `ToolRegistry.execute` is the only place where a tool call becomes an execution,
and it refuses before anything runs when the name is unknown, the arguments fail the Pydantic
schema (wrong type, extra field, value outside a `Literal`), or the tool is marked mutating
and no human confirmed. Refusals and network failures (503, timeout) go back to the model as
`is_error` observations, never as exceptions: the loop does not crash, the model explains or
corrects itself. `max_steps` bounds a model that loops; it stopped a 7B that wrote the same
registry call five times in a row.

Schema hygiene matters for the model too: Pydantic injects `title` and class docstrings into
JSON Schema, which is noise in the prompt and can contradict the description. `Tool.spec()`
strips them. A `Literal["champion"]` becomes a `const`: an invented alias (`challenger`) is
refused with the validation message, and the model retries with the right one.

No mutating tool exists yet; the mechanism is in place for `/reload`.

## 3. Two providers, one interface

`llm/types.py` is a neutral vocabulary (user, assistant with tool calls, tool result,
tool spec, reply). The agent, the tools, the graders and the tests only see that. Two
adapters translate: Anthropic (tools as `input_schema`, calls as `tool_use` blocks, results
as `tool_result` blocks grouped in one user message) and OpenAI-compatible for LM Studio
(tools wrapped in `{"type": "function"}`, calls with arguments as a JSON *string*, results as
`role: tool` messages). A third implementation, the scripted `FakeLLM` of the tests, is the
proof that nothing depends on a provider; the control brains of the evaluation are a fourth.

One adapter-level repair was needed by measurement: a 7B on LM Studio, asked to write one
sentence before each tool call, wrote the call itself as text (`[search_documentation]
{...} [END_TOOL_REQUEST]`) and the server dropped it. The model had decided right; the
transport lost the decision. The OpenAI-compatible adapter now salvages that pattern, and
live routing on that model went from 73 % to 90 % on the rows before its GPU driver died.

## 4. Retrieval: what actually improved it

Benchmark: 5 questions with a known expected section, hit@1 and hit@3.

| configuration | hit@1 | hit@3 | lesson |
|---|---|---|---|
| MiniLM, 1200-char chunks, full title path | 0/5 | 3/5 | 106 of 120 chunks silently truncated: MiniLM embeds 128 tokens, the median chunk had 271 |
| MiniLM, 600 chars, full title path | 0/5 | 0/5 | the title prefix ate a third of the window |
| MiniLM, 450 chars, two titles | 1/5 | 3/5 | better, still weak on this corpus |
| multilingual-e5-small (512 tokens) | 0–1/5 | 2–3/5 | not better, and non-discriminating scores ("pizza" at 0.83) |
| BM25 alone | 2/5 | 3/5 | exact identifiers (`min_delta`, `Wasserstein`, `X-TerraOps-Source`) |
| **hybrid, reciprocal rank fusion** | **2–3/5** | **3/5** | complementary; rank-based, so no score calibration |

Guards against over-retrieval live in code, not in the prompt: `k` defaults to 4 and is
capped at 6 by the schema, a relevance floor (cosine ≥ 0.25 or one query term present), at
most two chunks per section, and an explicit empty result the model must report as "the
documentation does not cover this". French and English stopwords were necessary: without
them, *"c'est quoi la dérive ?"* matched the whole corpus on *la* and *est*.

The benchmark does not measure the part that matters most: the model writes the query. On
the raw question the top hit was a Q&A section; when the model rephrases to *"what is data
drift"*, all four passages come from the concept section. The tool description guides that
rephrasing.

## 5. Evaluating an agent

A classifier has one input, one label, one equality. An agent has several valid routes
(`get_served_model` or `get_api_health` both give the served version), several valid
phrasings (*v1*, *version 1*, *98.1 %*, *0.981*), correct answers with no reference value
(*"I cannot"* is right for five questions), and it is stochastic. Hence, in `eval/cases.py`:
ground truth is a **function** resolved against the API at run time, never a constant; a
fact is a group of equivalent alternatives, normalized (accents, case, decimal comma, word
boundaries); `required_tools ⊂ allowed_tools` rather than an exact sequence; `--reps` to
see the variance.

**Route and outcome are separate columns**, never one score: a right answer by the wrong
route is luck, and luck does not ship. Grading the route is a deliberate choice here because
routing *is* the question; a production agent would be graded on its end state.

**Hallucination is deterministic where it can be**: a forbidden phrase (*"no drift"* when the
verdict is *inconclusive*), a number absent from every tool result and from the question, a
citation the tool never returned. The optional LLM judge only covers what code cannot see,
faithfulness to the retrieved passages and the quality of a refusal, with a length-bias
instruction, a configurable second model family against self-preference, the candidate
passed as delimited data, and no calibration yet against human labels. Its verdicts are
reported, not trusted.

Infrastructure failures (API down, driver crash, empty reply) go to `errors.jsonl`. *No
answer* is never scored as *wrong answer*; a category then reports its reduced `n`.

## 6. Validating the harness before the first cent

Three control brains run the same loop and the same tools. Their expected profile is known
in advance, so a wrong grader shows up as a wrong profile:

| control | tool choice | facts | citation | refusal | over-refusal | hallucination |
|---|---|---|---|---|---|---|
| oracle (perfect route and facts) | 100 | 100 | 100 | 100 | 0 | 0 |
| null ("I don't know") | 17 | 0 | 0 | 100 | 100 | 0 |
| liar (invented numbers, no tool) | 17 | 4 | 0 | 0 | 0 | 100 |

The 17 % tool choice of null and liar is the five refuse cases, where calling nothing is
right. The liar's 4 % facts is one case whose expected words are generic (*champion*, *gate*);
the hallucination column catches it. The liar found two lenient graders before any real run:
`1` matched inside `1234`, and *chargé* inside *rechargé*. Facts now require word boundaries
(liar facts 29 → 8 → 4 %). The controls are re-run after every grader change, and they call no
provider (`input_tokens: 0` in their reports).

## 7. Re-score, do not re-run

Every run saves its trajectories. `python evaluate.py --rescore <dir>` grades them again with
the current graders without calling any model, and stamps the report with the grader's git
commit (`meta.rescored_with_git_commit`). Eleven grader defects were found by reading rows
marked KO: trailing zeros (`0.9810` vs `0.981`), Markdown bold around a number, units
(*31,91ms* is not *31*; *p95* is not a number), timestamps read as numbers (*12:04:32*),
*24 h* counted as an invented figure, *"I cannot reload"* counted as *reloaded*, nuanced
refusals (*"not able to"*, *"impossible à savoir"*). About one KO row in three was the
grader's fault. Several defects only surfaced on Claude's richer answers: a grader calibrated
on small models under-scored the large one, from 15 % to 3 % hallucination once fixed.

Reports before and after a grader change are not comparable; that is why both the original
and the rescored version of every run are versioned.

## 8. What the runs say

Full tables in [eval/](eval/). The stable findings across runs:

- Local models do not hallucinate live facts (0 % in three runs out of four) but invent on
  refuse questions (*"next month's champion will be v1"*) and accept the false premise
  (*"the champion is v3 because…"*). Refusing and contradicting are harder than calling a tool.
- No local model called both tools on the two-tool question; Claude did, 2/2.
- A placeholder in a prompt is an instruction for a large model and an example to copy for a
  small one: with `cite as [source § section]` in the prompt, the 7B invented a citation in
  12 of 22 documentation answers; with a concrete example and a ban on citing without the
  tool, 3 of 11.
- The 3B is three times faster than the 7B on this laptop, finishes without driver crashes,
  and actually uses the documentation tool (55 % of documentation questions vs 14–18 %).
- Claude's four imperfect rows out of 58: two retrieval misses answered cautiously with real
  citations, one string-grader false positive (it wrote *"so this is not 'no drift'"*), and
  one debatable "closest approximation" on a refuse case. Documented, not patched away.
- Reference run cost: 336 896 input and 30 925 output tokens, $2.46 at list price, 10 s per
  question (5 s once the prompt cache is warm).

## 9. Demo and packaging

An agent is demonstrated by its route, not its answer: which tool, why, with what
arguments, what came back. The loop emits events (`thinking`, `tool_call` with the model's
one-sentence reason, `tool_result`, `answer`) and the UI renders them in order while they
happen. A refusal is a visible route too: *no tool called*, plus the model's sentence. The GIF
is recorded on that UI by Playwright, on a real provider.

The compose file *includes* TerraOps' own compose instead of copying it, under the same
project name, so the copilot joins the stack the platform already runs. The TerraOps
repository is mounted read-only for one reason: `get_drift_report` runs `drift_report.py`
as a subprocess, because there is no drift endpoint on that side. That is also why the image
is ~3 GB (torch, torchvision, Evidently); the right fix is a drift endpoint in TerraOps, a
documented debt there, not worked around here.

## 10. Known debt

- LLM adapters, `eval/runner.py`, `judge.py` and the HTTP client have no offline tests.
- The judge is not calibrated: ~30 hand-labelled answers and an agreement rate are the next step.
- 29 cases give ±13 points at two repetitions; a 5-point difference between two prompts is noise.
- The corpus snapshot must be refreshed when TerraOps' documentation changes, and the
  documentation cases re-checked against the new index.
- Five endpoints are not tools; `/metrics` will need parsing into a small JSON, never raw
  Prometheus text in the context window.
