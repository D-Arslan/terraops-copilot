"""Run the case set through the REAL agent entry point, grade, report.

Reproducibility contract (what the report records):
- dataset id + hash of the case questions, category counts;
- agent provider/model, judge provider/model (or 'deterministic only');
- ground truth as resolved at run time (so a later reader sees what 'v1' meant);
- full trajectory per (case, rep): every model turn, tool call, tool result, usage;
- errors in a sidecar (harness/serving failures never become '0 points');
- reps, so the headline carries a spread and not a point estimate.
"""
from __future__ import annotations

import hashlib
import json
import platform
import statistics
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..agent.loop import Agent, AgentResult, Step
from ..client.terraops_api import TerraOpsClient
from ..llm.types import AssistantMessage, ToolResultMessage, UserMessage
from .cases import CASES, Case, Expect
from .graders import Grade, grade, returned_citations
from .judge import Judge

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class Row:
    case_id: str
    category: str
    rep: int
    question: str
    answer: str
    expect: dict
    grade: dict
    judge: dict | None
    steps: int
    tools_called: list[str]
    usage: dict
    latency_s: float
    trajectory: list[dict]


@dataclass
class Summary:
    n_cases: int
    n_rows: int
    n_errors: int
    metrics: dict
    per_category: dict
    per_case: dict
    meta: dict = field(default_factory=dict)


def _serialise_messages(result: AgentResult) -> list[dict]:
    out = []
    for m in result.messages:
        if isinstance(m, UserMessage):
            out.append({"role": "user", "text": m.text})
        elif isinstance(m, AssistantMessage):
            out.append({"role": "assistant", "text": m.text,
                        "tool_calls": [{"name": c.name, "arguments": c.arguments} for c in m.tool_calls]})
        elif isinstance(m, ToolResultMessage):
            out.append({"role": "tool", "name": m.name, "is_error": m.is_error, "content": m.content})
    return out


def _expect_dict(e: Expect) -> dict:
    d = asdict(e)
    d["required_tools"], d["allowed_tools"] = sorted(e.required_tools), sorted(e.allowed_tools)
    return d


def _git_commit() -> str:
    """Code version the numbers belong to; grader changes make older reports incomparable."""
    import subprocess
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT,
                             capture_output=True, text=True, timeout=5)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT,
                               capture_output=True, text=True, timeout=5).stdout.strip()
        return (out.stdout.strip() or "n/a") + ("-dirty" if dirty else "")
    except Exception:
        return "n/a"


def dataset_hash(cases: list[Case]) -> str:
    h = hashlib.sha256("\n".join(f"{c.id}|{c.category}|{c.question}" for c in cases).encode("utf-8"))
    return h.hexdigest()[:12]


def run_case(agent: Agent, case: Case, exp: Expect, rep: int, judge: Judge | None) -> Row:
    bind = getattr(agent.llm, "bind", None)
    if bind:                       # oracle needs to know the expectations
        bind(case, exp)
    t0 = time.perf_counter()
    result = agent.run(case.question)
    latency = time.perf_counter() - t0
    g = grade(case.question, result, exp)
    usage = {"input_tokens": 0, "output_tokens": 0, "llm_calls": 0}
    for s in result.steps:
        usage["input_tokens"] += s.reply.usage.get("input_tokens", 0)
        usage["output_tokens"] += s.reply.usage.get("output_tokens", 0)
        usage["llm_calls"] += 1

    jd = None
    if judge is not None:
        jd = _judge(judge, case, result, g, exp)
    return Row(case_id=case.id, category=case.category, rep=rep, question=case.question,
               answer=result.answer, expect=_expect_dict(exp), grade=asdict(g), judge=jd,
               steps=len(result.steps), tools_called=result.tools_called, usage=usage,
               latency_s=round(latency, 3), trajectory=_serialise_messages(result))


def _judge(judge: Judge, case: Case, result: AgentResult, g: Grade, exp: Expect) -> dict:
    out: dict = {}
    if exp.cite:
        evidence = "\n\n".join(r.content for s in result.steps for r in s.results
                               if r.name == "search_documentation" and not r.is_error) or "(none)"
        v = judge.faithfulness(case.question, evidence, result.answer)
        out["faithfulness"] = {"ok": v.ok, **v.detail, "usage": v.usage}
        if not v.ok:
            g.hallucination = True
    if exp.refuse:
        v = judge.refusal(case.question, result.answer)
        out["refusal"] = {"ok": v.ok, **v.detail, "usage": v.usage}
        if not v.ok:
            g.refusal = False
        if v.detail.get("invents_fact_or_action"):
            g.hallucination = True
    return out


def _rate(values: list[bool | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return round(100.0 * sum(vals) / len(vals), 1) if vals else None


def summarise(rows: list[Row], errors: list[dict], cases: list[Case], meta: dict) -> Summary:
    def metrics_for(rs: list[Row]) -> dict:
        gs = [r.grade for r in rs]
        return {
            "n": len(rs),
            "tool_choice_pct": _rate([g["tool_choice"] for g in gs]),
            "factual_accuracy_pct": _rate([g["facts"] for g in gs]),
            "citation_pct": _rate([g["citation"] for g in gs]),
            "correct_refusal_pct": _rate([g["refusal"] for g in gs]),
            "over_refusal_pct": _rate([g["over_refusal"] for g in gs if g["facts"] is not None]),
            "hallucination_pct": _rate([g["hallucination"] for g in gs]),
            "mean_llm_calls": round(statistics.mean(r.usage["llm_calls"] for r in rs), 2) if rs else None,
            "mean_latency_s": round(statistics.mean(r.latency_s for r in rs), 2) if rs else None,
            "input_tokens": sum(r.usage["input_tokens"] for r in rs),
            "output_tokens": sum(r.usage["output_tokens"] for r in rs),
        }

    per_cat = {cat: metrics_for([r for r in rows if r.category == cat])
               for cat in sorted({c.category for c in cases})}
    per_case = {}
    for c in cases:
        rs = [r for r in rows if r.case_id == c.id]
        if rs:
            per_case[c.id] = {"category": c.category,
                              "facts": _rate([r.grade["facts"] for r in rs]),
                              "tool_choice": _rate([r.grade["tool_choice"] for r in rs]),
                              "hallucination": _rate([r.grade["hallucination"] for r in rs]),
                              "refusal": _rate([r.grade["refusal"] for r in rs]),
                              "citation": _rate([r.grade["citation"] for r in rs]),
                              "tools": sorted({t for r in rs for t in r.tools_called})}
    return Summary(n_cases=len(cases), n_rows=len(rows), n_errors=len(errors),
                   metrics=metrics_for(rows), per_category=per_cat, per_case=per_case, meta=meta)


def run(agent: Agent, cases: list[Case], reps: int, judge: Judge | None, out_dir: Path,
        client: TerraOpsClient, label: str) -> Summary:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[Row] = []
    errors: list[dict] = []
    truths: dict[str, dict] = {}
    total = len(cases) * reps
    t_start = time.perf_counter()

    # Rows and errors are APPENDED as they happen: a run killed half-way (or a slow
    # local model) still leaves scorable data, and progress is visible from the files.
    results_f = (out_dir / "results.jsonl").open("w", encoding="utf-8")
    errors_f = (out_dir / "errors.jsonl").open("w", encoding="utf-8")
    try:
        for case in cases:
            try:
                exp = case.resolve(client)                 # ground truth from the live system
            except Exception as exc:
                err = {"case_id": case.id, "phase": "ground_truth", "error": repr(exc)}
                errors.append(err)
                errors_f.write(json.dumps(err, ensure_ascii=False) + "\n"); errors_f.flush()
                continue
            truths[case.id] = _expect_dict(exp)
            for rep in range(reps):
                try:
                    row = run_case(agent, case, exp, rep, judge)
                    rows.append(row)
                    results_f.write(json.dumps(asdict(row), ensure_ascii=False) + "\n"); results_f.flush()
                    mark = "ok " if (row.grade["facts"] in (True, None) and row.grade["tool_choice"]
                                     and not row.grade["hallucination"]) else "KO "
                    done = len(rows) + len(errors)
                    eta = (time.perf_counter() - t_start) / done * (total - done)
                    print(f"[{mark}] {case.id:<10} rep{rep} tools={row.tools_called} "
                          f"facts={row.grade['facts']} halluc={row.grade['hallucination']} "
                          f"({done}/{total}, {row.latency_s:.0f}s, ETA {eta/60:.0f} min)", flush=True)
                except Exception as exc:
                    err = {"case_id": case.id, "rep": rep, "phase": "agent",
                           "error": repr(exc), "trace": traceback.format_exc()[-1500:]}
                    errors.append(err)
                    errors_f.write(json.dumps(err, ensure_ascii=False) + "\n"); errors_f.flush()
                    print(f"[ERR] {case.id} rep{rep}: {exc!r}", flush=True)
    finally:
        results_f.close()
        errors_f.close()

    meta = {
        "label": label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agent_llm": f"{agent.llm.name}/{getattr(agent.llm, 'model', '?')}",
        "judge_llm": f"{judge.llm.name}/{getattr(judge.llm, 'model', '?')}" if judge else "none (deterministic only)",
        "dataset_hash": dataset_hash(cases),
        "categories": {cat: sum(1 for c in cases if c.category == cat) for cat in sorted({c.category for c in cases})},
        "reps": reps,
        "python": platform.python_version(),
        "argv": sys.argv,
        "ground_truth": truths,
        "system_prompt_sha": hashlib.sha256(agent.system_prompt.encode()).hexdigest()[:12],
        "git_commit": _git_commit(),
        "tools_offered": [s.name for s in agent.registry.specs()],
    }
    summary = summarise(rows, errors, cases, meta)

    (out_dir / "summary.json").write_text(json.dumps(asdict(summary), ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(summary, rows), encoding="utf-8")
    return summary


def render_report(s: Summary, rows: list[Row]) -> str:
    m, meta = s.metrics, s.meta
    L = [f"# TerraOps Copilot — evaluation report ({meta['label']})", "",
         f"- generated: {meta["generated_at"]} · code: `{meta.get("git_commit", "n/a")}`",
         f"- agent: `{meta['agent_llm']}` · judge: `{meta['judge_llm']}`",
         f"- dataset: {s.n_cases} cases (hash `{meta['dataset_hash']}`) · {meta['categories']} · reps={meta['reps']}",
         f"- rows scored: {s.n_rows} · errors (not scored): {s.n_errors}",
         f"- tools offered: {', '.join(meta['tools_offered'])} · system prompt sha `{meta['system_prompt_sha']}`", "",
         "## Headline", "",
         "| metric | value |", "|---|---|",
         f"| tool choice correct | {m['tool_choice_pct']} % |",
         f"| factual accuracy (live+rag+mixed+trap) | {m['factual_accuracy_pct']} % |",
         f"| citation present & real (rag) | {m['citation_pct']} % |",
         f"| correct refusal (refuse cases) | {m['correct_refusal_pct']} % |",
         f"| over-refusal (answerable cases) | {m['over_refusal_pct']} % |",
         f"| hallucination (any case) | {m['hallucination_pct']} % |",
         f"| mean LLM calls / question | {m['mean_llm_calls']} |",
         f"| mean latency (s) | {m['mean_latency_s']} |",
         f"| tokens in / out | {m['input_tokens']} / {m['output_tokens']} |", "",
         "## Per category", "",
         "| category | n | tool choice | facts | citation | refusal | over-refusal | hallucination |",
         "|---|---|---|---|---|---|---|---|"]
    for cat, cm in s.per_category.items():
        L.append(f"| {cat} | {cm['n']} | {cm['tool_choice_pct']} | {cm['factual_accuracy_pct']} | "
                 f"{cm['citation_pct']} | {cm['correct_refusal_pct']} | {cm['over_refusal_pct']} | "
                 f"{cm['hallucination_pct']} |")
    L += ["", "## Per case", "", "| case | cat | tools called | facts | tool choice | citation | refusal | halluc |",
          "|---|---|---|---|---|---|---|---|"]
    for cid, pc in s.per_case.items():
        L.append(f"| {cid} | {pc['category']} | {', '.join(pc['tools']) or '—'} | {pc['facts']} | "
                 f"{pc['tool_choice']} | {pc['citation']} | {pc['refusal']} | {pc['hallucination']} |")
    L += ["", "## Failures (first rep)", ""]
    shown = 0
    for r in rows:
        g = r.grade
        bad = (g["facts"] is False) or (not g["tool_choice"]) or g["hallucination"] or (g["refusal"] is False)
        if r.rep == 0 and bad:
            L += [f"### {r.case_id} — {r.question}", f"- tools: {r.tools_called}",
                  f"- missing facts: {g['missing_facts']} · forbidden: {g['forbidden_hit']} · "
                  f"unsupported numbers: {g['unsupported_numbers']}",
                  f"- answer: {r.answer[:400].replace(chr(10), ' ')}", ""]
            shown += 1
    if not shown:
        L.append("(none)")
    L += ["", "## How to read", "",
          "- *tool choice* grades the ROUTE: required tools called, no disallowed tool.",
          "- *facts* grades the OUTCOME against ground truth fetched from the API at run time.",
          "- *hallucination* = forbidden phrase, number absent from every tool result, invented citation,"
          " or (with a judge) a claim unsupported by the retrieved passages.",
          "- Errors (API down, exceptions) are in errors.jsonl and never counted as wrong answers.",
          f"- Ground truth snapshot is in summary.json → meta.ground_truth."]
    return "\n".join(L) + "\n"


# --- re-scoring -----------------------------------------------------------------

def rescore(run_dir: Path, cases: list[Case]) -> Summary:
    """Re-grade an existing run from its saved trajectories, WITHOUT calling any model.

    Use after a grader fix: the model's answers are what they were, only the scoring
    changes. Writes summary.rescored.json + report.rescored.md next to the originals,
    and records which grader version (git commit) produced them.
    """
    from ..llm.types import LLMReply, ToolCall, ToolResultMessage
    from .cases import Expect

    rows: list[Row] = []
    for line in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        exp = Expect(required_tools=set(d["expect"]["required_tools"]),
                     allowed_tools=set(d["expect"]["allowed_tools"]),
                     facts=d["expect"]["facts"], forbidden=d["expect"]["forbidden"],
                     cite=d["expect"]["cite"], refuse=d["expect"]["refuse"])
        # rebuild the minimal AgentResult the graders need (tool calls + results)
        steps: list[Step] = []
        for m in d["trajectory"]:
            if m["role"] == "assistant":
                calls = [ToolCall(id=f"r{i}", name=c["name"], arguments=c["arguments"])
                         for i, c in enumerate(m["tool_calls"])]
                steps.append(Step(LLMReply(text=m["text"], tool_calls=calls, stop_reason="")))
            elif m["role"] == "tool" and steps:
                steps[-1].results.append(ToolResultMessage(call_id="", name=m["name"],
                                                           content=m["content"], is_error=m["is_error"]))
        res = AgentResult(answer=d["answer"], steps=steps, messages=[])
        g = grade(d["question"], res, exp)
        d["grade"] = asdict(g)
        rows.append(Row(**d))
    errors = [json.loads(l) for l in (run_dir / "errors.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    old = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    meta = {**old["meta"], "rescored_at": datetime.now(timezone.utc).isoformat(),
            "rescored_with_git_commit": _git_commit(), "label": old["meta"]["label"] + " (rescored)"}
    summary = summarise(rows, errors, cases, meta)
    (run_dir / "summary.rescored.json").write_text(json.dumps(asdict(summary), ensure_ascii=False, indent=2),
                                                   encoding="utf-8")
    (run_dir / "report.rescored.md").write_text(render_report(summary, rows), encoding="utf-8")
    return summary
