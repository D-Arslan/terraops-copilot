"""Evaluate the TerraOps Copilot agent.  `python evaluate.py [--agent real|oracle|null|liar]`

Examples
  python evaluate.py --agent oracle           # harness self-test: must be ~100 %
  python evaluate.py --agent null             # must be ~0 % facts, 100 % refusal
  python evaluate.py --agent liar             # must light up hallucination
  python evaluate.py --reps 2 --judge         # the real agent (LLM_PROVIDER from .env)
  python evaluate.py --only rag,refuse --limit 5

Requires the TerraOps stack up and the vector store built (rag.ingest).
Outputs: eval_reports/<timestamp>_<label>/{report.md, summary.json, results.jsonl, errors.jsonl}
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from terraops_copilot.agent.loop import Agent                       # noqa: E402
from terraops_copilot.cli import build_agent                         # noqa: E402
from terraops_copilot.client.terraops_api import TerraOpsClient      # noqa: E402
from terraops_copilot.eval.baselines import LiarLLM, NullLLM, OracleLLM  # noqa: E402
from terraops_copilot.eval.cases import CASES                        # noqa: E402
from terraops_copilot.eval.judge import make_judge                   # noqa: E402
from terraops_copilot.eval.runner import run                         # noqa: E402


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", default="real", choices=["real", "oracle", "null", "liar"])
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--judge", action="store_true", help="add LLM-as-a-judge for faithfulness/refusal")
    ap.add_argument("--only", default=None, help="comma-separated categories or case ids")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", type=Path, default=Path("eval_reports"))
    args = ap.parse_args(argv)

    cases = CASES
    if args.only:
        keys = {k.strip() for k in args.only.split(",")}
        cases = [c for c in cases if c.category in keys or c.id in keys]
    if args.limit:
        cases = cases[: args.limit]

    agent = build_agent(with_rag=True)
    if args.agent != "real":
        brain = {"oracle": OracleLLM, "null": NullLLM, "liar": LiarLLM}[args.agent]()
        agent = Agent(brain, agent.registry, max_steps=agent.max_steps, system_prompt=agent.system_prompt)
    judge = make_judge() if args.judge else None

    label = args.agent if args.agent != "real" else os.getenv("LLM_PROVIDER", "anthropic")
    out_dir = args.out / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{label}"
    client = TerraOpsClient()
    client.wait_ready()

    summary = run(agent, cases, args.reps, judge, out_dir, client, label)
    m = summary.metrics
    print(f"\n{'=' * 64}\n{label}: {summary.n_rows} rows, {summary.n_errors} errors")
    print(f"tool choice {m['tool_choice_pct']} % | facts {m['factual_accuracy_pct']} % | "
          f"citation {m['citation_pct']} % | refusal {m['correct_refusal_pct']} % | "
          f"over-refusal {m['over_refusal_pct']} % | hallucination {m['hallucination_pct']} %")
    print(f"report -> {out_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
