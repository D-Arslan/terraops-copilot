"""`python -m terraops_copilot "quel est le modèle champion actuel ?"`

--trace prints every model turn and tool result: this is how you SEE the loop.
"""
from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from .agent.loop import Agent
from .client.terraops_api import TerraOpsClient
from .llm.factory import make_llm_client
from .tools.base import ToolRegistry
from .tools.drift import build_drift_tool
from .tools.terraops import build_tools


def build_agent(with_rag: bool = True) -> Agent:
    client = TerraOpsClient()
    tools = build_tools(client) + [build_drift_tool()]
    if with_rag:
        from .rag.ingest import store_path
        from .rag.store import HybridRetriever, VectorStore, sentence_transformer_embedder
        from .tools.docs import build_docs_tool
        store = VectorStore(store_path(), sentence_transformer_embedder())
        if store.count() == 0:
            raise SystemExit("Vector store is empty: run `python -m terraops_copilot.rag.ingest` first.")
        tools.append(build_docs_tool(HybridRetriever(store)))
    return Agent(make_llm_client(), ToolRegistry(tools))


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    ap = argparse.ArgumentParser(prog="terraops-copilot")
    ap.add_argument("question", nargs="+")
    ap.add_argument("--trace", action="store_true", help="show tool calls and results")
    ap.add_argument("--no-rag", action="store_true", help="API tools only (no vector store)")
    args = ap.parse_args(argv)

    agent = build_agent(with_rag=not args.no_rag)
    result = agent.run(" ".join(args.question))

    if args.trace:
        print(f"[llm] {agent.llm.name} / {getattr(agent.llm, 'model', '?')}")
        for i, step in enumerate(result.steps, 1):
            r = step.reply
            print(f"[step {i}] stop={r.stop_reason} usage={r.usage}")
            if r.text:
                print(f"  text: {r.text[:300]}")
            for call, res in zip(r.tool_calls, step.results):
                flag = "ERROR" if res.is_error else "ok"
                print(f"  call {call.name}({call.arguments}) -> {flag}: {res.content[:300]}")
        print("-" * 60)
    print(result.answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
