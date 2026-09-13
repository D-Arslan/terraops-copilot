# Evaluation reports

Versioned copies of the runs cited in the main README, so every number there can be
checked from the repository. `eval_reports/` (the live output directory) stays ignored.

| directory | agent | rows | what it is |
|---|---|---|---|
| `20260911T174119Z_anthropic` | Claude Opus 5, 2 reps | 58 | reference measurement |
| `20260911T144057Z_lmstudio` | Qwen2.5-3B-instruct | 29 | best complete local run |
| `20260911T135137Z_lmstudio` | Qwen2.5-coder-7B | 10 (+5 errors) | best partial 7B run, adapter salvage on |
| `20260911T094019Z_lmstudio` | Qwen2.5-coder-7B, prompt v1 | 50 (+8 errors) | invented-citation evidence |
| `20260911T123048Z_lmstudio` | Qwen2.5-coder-7B, prompt v2 | 29 | prompt v2 effect |
| `20260913T194254Z_oracle` | control: perfect route and facts | 29 | must score 100 / 100 / 100 / 100 / 0 / 0 |
| `20260913T194355Z_null` | control: always "I don't know" | 29 | must score 0 facts, 100 refusal |
| `20260913T194435Z_liar` | control: invented numbers | 29 | must score 100 hallucination |

Files per run:

- `summary.json`, `report.md`: scores as produced at run time, with the grader of that day.
- `summary.rescored.json`, `report.rescored.md`: the same answers graded again with the
  graders at commit `21128ae` (`python evaluate.py --rescore <dir>`; the stamp is in
  `meta.rescored_with_git_commit`). The README table uses these.
- `errors.jsonl`: rows that failed for infrastructure reasons (model server crash,
  timeout); never scored as wrong answers.

Not versioned: `results.jsonl` (full trajectories with every tool output). Ask if needed.

The controls are re-run after every grader change; those here match the graders used for
the rescored numbers. Control runs call no LLM provider (`input_tokens: 0`).
