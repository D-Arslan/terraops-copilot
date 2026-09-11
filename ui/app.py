"""TerraOps Copilot — Streamlit chat that shows the agent THINKING.

What the demo has to make visible in one glance:
  1. which tool the agent picks, and the sentence that says why;
  2. the real call to TerraOps (arguments, raw result) or the RAG passages;
  3. the answer, with its citations.
The UI is a thin client of the Agent: it only renders the events the loop emits.

Run: streamlit run ui/app.py  (TerraOps up, vector store built, provider in .env)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from terraops_copilot.cli import build_agent                      # noqa: E402
from terraops_copilot.client.terraops_api import TerraOpsClient   # noqa: E402

st.set_page_config(page_title="TerraOps Copilot", page_icon="🛰️", layout="wide")

TOOL_ICON = {"search_documentation": "📚", "get_drift_report": "📈", "get_registry_champion": "🏆",
             "get_served_model": "🧠", "get_api_health": "💓"}
TOOL_KIND = {"search_documentation": "documentation (RAG)"}
EXAMPLES = [
    "Quel est le modèle champion actuel ?",
    "C'est quoi la dérive (data drift) ?",
    "Y a-t-il de la dérive cette semaine ?",
    "Le modèle servi est-il bien le champion du registry ?",
    "Quelle est la latence p95 de l'API sur la dernière heure ?",
]


@st.cache_resource(show_spinner="Chargement de l'agent (modèle d'embedding, index)…")
def get_agent():
    return build_agent(with_rag=True)


def latest_eval() -> dict | None:
    reports = sorted((ROOT / "eval_reports").glob("*/summary.json")) if (ROOT / "eval_reports").exists() else []
    real = [p for p in reports if not any(k in p.parent.name for k in ("oracle", "null", "liar"))]
    if not real:
        return None
    latest = real[-1]
    # A re-scored summary (graders fixed after the run) supersedes the original one.
    rescored = latest.with_name("summary.rescored.json")
    return json.loads((rescored if rescored.exists() else latest).read_text(encoding="utf-8"))


def kind_of(tool: str) -> str:
    return TOOL_KIND.get(tool, "donnée live (API TerraOps)")


def render_tool_result(name: str, content: str, is_error: bool) -> None:
    if is_error:
        st.error(content[:600])
        return
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        st.code(content[:800])
        return
    if name == "search_documentation":
        passages = data.get("passages", [])
        if not passages:
            st.warning("Aucun passage pertinent dans la documentation.")
        for p in passages:
            with st.container(border=True):
                st.markdown(f"**📎 {p['citation']}**  ·  _{', '.join(p.get('matched_by', []))}_")
                st.caption(p["text"][:700] + ("…" if len(p["text"]) > 700 else ""))
    else:
        st.json(data, expanded=True)


def run_question(agent, question: str) -> dict:
    """Run the agent, rendering each event as it happens. Returns a serialisable turn."""
    turn = {"question": question, "events": [], "answer": ""}
    status = st.status("🤔 L'agent réfléchit…", expanded=True)

    def on_event(event):
        kind, payload = event
        with status:
            if kind == "tool_call":
                call, reason = payload["call"], payload["reason"]
                icon = TOOL_ICON.get(call.name, "🛠️")
                if reason:
                    st.markdown(f"💬 *{reason.strip()}*")
                st.markdown(f"{icon} **Outil choisi : `{call.name}`** — {kind_of(call.name)}")
                if call.arguments:
                    st.code(json.dumps(call.arguments, ensure_ascii=False), language="json")
                turn["events"].append({"type": "tool_call", "name": call.name,
                                       "arguments": call.arguments, "reason": reason})
            elif kind == "tool_result":
                with st.expander(f"↩️ Résultat de `{payload.name}`", expanded=True):
                    render_tool_result(payload.name, payload.content, payload.is_error)
                turn["events"].append({"type": "tool_result", "name": payload.name,
                                       "content": payload.content, "is_error": payload.is_error})
            elif kind == "answer":
                status.update(label="✅ Réponse prête", state="complete", expanded=True)

    result = agent.run(question, on_event=on_event)
    turn["answer"] = result.answer
    turn["tools"] = result.tools_called
    if not result.tools_called:
        with status:
            st.markdown("🚫 **Aucun outil appelé** — l'agent répond directement (ou refuse).")
    return turn


def render_turn(turn: dict) -> None:
    """Re-render a past turn from its recorded events (history)."""
    with st.status("🧭 Raisonnement", expanded=True, state="complete"):   # the route IS the demo
        for ev in turn["events"]:
            if ev["type"] == "tool_call":
                if ev.get("reason"):
                    st.markdown(f"💬 *{ev['reason'].strip()}*")
                st.markdown(f"{TOOL_ICON.get(ev['name'], '🛠️')} **`{ev['name']}`** — {kind_of(ev['name'])}")
                if ev["arguments"]:
                    st.code(json.dumps(ev["arguments"], ensure_ascii=False), language="json")
            else:
                with st.expander(f"↩️ Résultat de `{ev['name']}`", expanded=False):
                    render_tool_result(ev["name"], ev["content"], ev["is_error"])
        if not turn.get("tools"):
            st.markdown("🚫 **Aucun outil appelé**")
    st.markdown(turn["answer"])


# --- sidebar -------------------------------------------------------------------
with st.sidebar:
    st.title("🛰️ TerraOps Copilot")
    st.caption("Agent LLM · tool use + RAG hybride · au-dessus de la plateforme MLOps TerraOps")
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    st.markdown(f"**LLM :** `{provider}`")
    try:
        h = TerraOpsClient().health()
        st.success(f"TerraOps API · modèle v{h.get('model_version')} chargé" if h.get("model_loaded")
                   else "TerraOps API up · modèle NON chargé")
    except Exception as exc:
        st.error(f"TerraOps API injoignable : {type(exc).__name__}")
    ev = latest_eval()
    if ev:
        m = ev["metrics"]
        st.markdown("**Dernière évaluation (vrai agent)**")
        st.markdown(f"- outil correct : **{m['tool_choice_pct']} %**\n- exactitude : **{m['factual_accuracy_pct']} %**\n"
                    f"- hallucination : **{m['hallucination_pct']} %**\n- refus corrects : **{m['correct_refusal_pct']} %**")
        st.caption(f"{ev['n_cases']} cas · {ev['meta']['agent_llm']}")
    with st.expander("Outils exposés au modèle"):
        try:
            for spec in get_agent().registry.specs():
                st.markdown(f"{TOOL_ICON.get(spec.name, '🛠️')} **`{spec.name}`**")
                st.caption(spec.description[:220] + "…")
        except Exception as exc:
            st.error(str(exc))
    st.markdown("**Essayez :**")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True):
            st.session_state["pending"] = ex
    if st.button("🧹 Effacer la conversation"):
        st.session_state["turns"] = []

# --- chat ------------------------------------------------------------------------
st.session_state.setdefault("turns", [])
for turn in st.session_state["turns"]:
    with st.chat_message("user"):
        st.markdown(turn["question"])
    with st.chat_message("assistant"):
        render_turn(turn)

question = st.chat_input("Posez une question sur TerraOps (état live ou concept)…")
if not question and st.session_state.get("pending"):
    question = st.session_state.pop("pending")

if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        try:
            turn = run_question(get_agent(), question)
            st.markdown(turn["answer"])
            st.session_state["turns"].append(turn)
        except Exception as exc:
            st.error(f"Erreur : {type(exc).__name__}: {exc}")
