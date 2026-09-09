"""The evaluation set: 28 cases, four categories, ground truth resolved at run time.

Why ground truth is a FUNCTION and not a literal: the agent is asked about a live
system, so the reference answer must be fetched from that same system at eval time,
through our own client (never through the agent). Ask the API 'what version is
served', then check the agent said the same. The dataset stays valid after a new
champion is promoted; a hard-coded '1' would silently rot.

Categories
- live    : answerable only by calling a live tool; facts checked against the API.
- rag     : conceptual, answerable from the documentation; must cite; facts checked
            against terms known to be in the corpus (params.yaml, learning.md).
- mixed   : needs a live tool AND a comparison / second tool.
- refuse  : no tool can answer (missing capability, out of scope, future, action
            the agent cannot perform) -> the right answer is a clear 'I cannot',
            with no invented number.
- trap    : a false premise the agent must correct with live data.

Expectation vocabulary (see graders.py):
- required_tools : every one of these must have been called (any order).
- allowed_tools  : the only tools that may be called (a wrong-tool call fails
                   tool_choice even if the final answer is right - we grade the
                   route here on purpose, that is the sprint's question).
- facts          : list of alternative-groups; each group must be matched by at
                   least one of its alternatives (case/accents-insensitive).
- forbidden      : phrases that make the answer wrong even if facts match.
- cite           : answer must contain a [source § section] citation that
                   matches a passage the tool actually returned.
- refuse         : answer must contain a refusal marker and no unsupported number.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from ..client.terraops_api import TerraOpsClient
from ..tools.drift import DriftArgs, run_drift_report
from ..tools.terraops import REGISTRY_MODEL

Facts = list[list[str]]
Truth = dict


@dataclass
class Expect:
    required_tools: set[str] = field(default_factory=set)
    allowed_tools: set[str] = field(default_factory=set)
    facts: Facts = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    cite: bool = False
    refuse: bool = False


@dataclass
class Case:
    id: str
    category: str
    question: str
    # ground truth -> Expect, computed at run time from the live system
    resolve: Callable[[TerraOpsClient], Expect]
    note: str = ""


LIVE_READ = {"get_api_health", "get_served_model", "get_registry_champion", "get_drift_report"}
DOCS = {"search_documentation"}


def _num_alts(x: float | str) -> list[str]:
    """0.981 -> ['0.981', '0,981', '98.1', '98,1'] so unit/format choices don't fail a fact."""
    v = float(x)
    alts = {f"{v:.4f}".rstrip("0").rstrip("."), f"{v:.3f}".rstrip("0").rstrip("."),
            f"{v:.2f}".rstrip("0").rstrip(".")}
    if v <= 1.0:
        p = v * 100
        alts |= {f"{p:.2f}".rstrip("0").rstrip("."), f"{p:.1f}".rstrip("0").rstrip("."),
                 f"{p:.0f}"}
    return sorted({a for s in alts for a in (s, s.replace(".", ","))})


# --- live ---------------------------------------------------------------------

def served_version(c: TerraOpsClient) -> Expect:
    v = c.model_info()["model_version"]
    return Expect(required_tools={"get_served_model"},
                  allowed_tools={"get_served_model", "get_api_health"},
                  facts=[[f"version {v}", f"v{v}", f" {v}"]])


def api_up(c: TerraOpsClient) -> Expect:
    h = c.health()
    yes = ["chargé", "charge", "loaded", "oui", "yes", "opérationnel", "tourne", "up"]
    return Expect(required_tools={"get_api_health"},
                  allowed_tools={"get_api_health", "get_served_model"},
                  facts=[yes] if h["model_loaded"] else [["pas chargé", "not loaded", "non"]])


def champion_version(c: TerraOpsClient) -> Expect:
    v = c.registry_model_by_alias(REGISTRY_MODEL, "champion")["version"]
    return Expect(required_tools={"get_registry_champion"},
                  allowed_tools={"get_registry_champion", "get_served_model"},
                  facts=[[f"version {v}", f"v{v}", f" {v}"]])


def champion_gate_accuracy(c: TerraOpsClient) -> Expect:
    mv = c.registry_model_by_alias(REGISTRY_MODEL, "champion")
    acc = {t["key"]: t["value"] for t in mv["tags"]}["gate_accuracy"]
    return Expect(required_tools={"get_registry_champion"},
                  allowed_tools={"get_registry_champion"}, facts=[_num_alts(acc)])


def champion_run_id(c: TerraOpsClient) -> Expect:
    rid = c.registry_model_by_alias(REGISTRY_MODEL, "champion")["run_id"]
    return Expect(required_tools={"get_registry_champion"},
                  allowed_tools={"get_registry_champion"}, facts=[[rid[:8]]])


def num_classes(c: TerraOpsClient) -> Expect:
    n = c.model_info()["num_classes"]
    return Expect(required_tools={"get_served_model"}, allowed_tools={"get_served_model"},
                  facts=[[f"{n} classes", f"{n} catégories", f" {n} "]])


def class_list(c: TerraOpsClient) -> Expect:
    classes = c.model_info()["classes"]
    return Expect(required_tools={"get_served_model"}, allowed_tools={"get_served_model"},
                  facts=[[k] for k in classes])


def device(c: TerraOpsClient) -> Expect:
    d = c.model_info()["device"]
    return Expect(required_tools={"get_served_model"}, allowed_tools={"get_served_model"},
                  facts=[[d]])


def image_size(c: TerraOpsClient) -> Expect:
    s = c.model_info()["image_size"]
    return Expect(required_tools={"get_served_model"}, allowed_tools={"get_served_model"},
                  facts=[[str(s)]])


def drift_this_week(c: TerraOpsClient) -> Expect:
    r = run_drift_report(DriftArgs(since_days=7))
    if r["verdict"] == "inconclusive":
        return Expect(required_tools={"get_drift_report"}, allowed_tools={"get_drift_report"},
                      facts=[[str(r["n_rows_in_window"])], [str(r["min_rows_required"])]],
                      forbidden=["pas de dérive", "aucune dérive", "no drift", "pas de drift"])
    if r["verdict"] == "drift":
        return Expect(required_tools={"get_drift_report"}, allowed_tools={"get_drift_report"},
                      facts=[["dérive", "drift"]], forbidden=["pas de dérive", "no drift"])
    return Expect(required_tools={"get_drift_report"}, allowed_tools={"get_drift_report"},
                  facts=[["pas de dérive", "aucune dérive", "no drift"]])


def rows_this_week(c: TerraOpsClient) -> Expect:
    r = run_drift_report(DriftArgs(since_days=7))
    return Expect(required_tools={"get_drift_report"}, allowed_tools={"get_drift_report"},
                  facts=[[str(r["n_rows_in_window"])]])


def served_is_champion(c: TerraOpsClient) -> Expect:
    s = c.model_info()["model_version"]
    r = c.registry_model_by_alias(REGISTRY_MODEL, "champion")["version"]
    same = s == r
    return Expect(required_tools={"get_served_model", "get_registry_champion"},
                  allowed_tools={"get_served_model", "get_registry_champion"},
                  facts=[[f" {s}"], ["oui", "yes", "bien", "identique", "même", "same"] if same
                         else ["non", "no", "diff", "pas"]])


def false_premise_v3(c: TerraOpsClient) -> Expect:
    r = c.registry_model_by_alias(REGISTRY_MODEL, "champion")["version"]
    return Expect(required_tools={"get_registry_champion"},
                  allowed_tools={"get_registry_champion", "get_served_model", "search_documentation"},
                  facts=[[f"version {r}", f"v{r}", f" {r}"]],
                  forbidden=["est bien la version 3", "est la version 3", "champion est la v3"])


# --- rag (facts known to be in the committed corpus) ----------------------------

def rag(facts: Facts, extra_allowed: set[str] | None = None) -> Callable[[TerraOpsClient], Expect]:
    def _r(_c: TerraOpsClient) -> Expect:
        return Expect(required_tools=DOCS, allowed_tools=DOCS | (extra_allowed or set()),
                      facts=facts, cite=True)
    return _r


# --- refuse ---------------------------------------------------------------------

def refuse(allowed: set[str] | None = None, forbidden: list[str] | None = None):
    def _r(_c: TerraOpsClient) -> Expect:
        return Expect(allowed_tools=allowed or set(), refuse=True, forbidden=forbidden or [])
    return _r


CASES: list[Case] = [
    # live -----------------------------------------------------------------
    Case("live-01", "live", "Quelle version du modèle est servie par l'API en ce moment ?", served_version),
    Case("live-02", "live", "Est-ce que l'API tourne et le modèle est-il chargé ?", api_up),
    Case("live-03", "live", "Quel est le modèle champion actuel dans le registry MLflow ?", champion_version),
    Case("live-04", "live", "Quelle accuracy le champion a-t-il obtenue au gate de promotion ?", champion_gate_accuracy),
    Case("live-05", "live", "Quel est le run_id MLflow du champion ?", champion_run_id),
    Case("live-06", "live", "Combien de classes le modèle servi sait-il reconnaître ?", num_classes),
    Case("live-07", "live", "Liste-moi les classes que le modèle servi reconnaît.", class_list),
    Case("live-08", "live", "Sur quel device (CPU ou GPU) tourne l'inférence ?", device),
    Case("live-09", "live", "Quelle taille d'image le modèle attend-il en entrée ?", image_size),
    Case("live-10", "live", "Y a-t-il de la dérive cette semaine ?", drift_this_week,
         note="the honest answer may be 'inconclusive'; saying 'no drift' is a hallucination"),
    Case("live-11", "live", "Combien de prédictions ont été journalisées ces 7 derniers jours ?", rows_this_week),
    # mixed ----------------------------------------------------------------
    Case("mixed-01", "mixed", "Le modèle servi par l'API est-il bien le champion du registry ?", served_is_champion),
    # trap (false premise, live data corrects it) ---------------------------
    Case("trap-01", "trap", "Pourquoi le champion actuel est-il la version 3 ?", false_premise_v3),
    # rag ------------------------------------------------------------------
    Case("rag-01", "rag", "C'est quoi la dérive (data drift) ?",
         rag([["distribution", "entrée", "input", "données"]])),
    Case("rag-02", "rag", "Comment fonctionne la promotion d'un modèle (le gate champion/challenger) ?",
         rag([["champion"], ["challenger", "gate"]])),
    Case("rag-03", "rag", "Pourquoi TerraOps utilise Wasserstein plutôt qu'un test à p-value ?",
         rag([["volume", "taille", "effet", "effect", "échantillon", "n ="]])),
    Case("rag-04", "rag", "Quels sont les seuils du gate de promotion (min_accuracy et min_delta) ?",
         rag([_num_alts(0.90), _num_alts(0.003)])),
    Case("rag-05", "rag", "C'est quoi le train/serving skew et comment TerraOps l'évite ?",
         rag([["preprocessing", "prétraitement", "contrat"]])),
    Case("rag-06", "rag", "Pourquoi la version 3 a-t-elle été refusée par le gate ?",
         rag([["marge", "delta"], ["classe"]], extra_allowed={"get_registry_champion"})),
    Case("rag-07", "rag", "Quelle accuracy la version 4 avait-elle au gate, et pourquoi a-t-elle été refusée ?",
         rag([_num_alts(0.9765), ["marge", "delta", "0.44", "0,44"]], extra_allowed={"get_registry_champion"})),
    Case("rag-08", "rag", "Quel est l'angle mort du flou (blur) dans le monitoring de dérive ?",
         rag([["colorim", "couleur", "color", "texture", "radiom"]])),
    Case("rag-09", "rag", "Que fait le rapport de dérive quand il n'y a pas assez de données ?",
         rag([["refuse", "conclu", "200"]], extra_allowed={"get_drift_report"})),
    Case("rag-10", "rag", "Combien de fenêtres consécutives en dérive faut-il avant de déclencher un réentraînement ?",
         rag([["3", "trois"]])),
    Case("rag-11", "rag", "Quelle accuracy le modèle d'origine avait-il sur le jeu de test EuroSAT ?",
         rag([_num_alts(0.978)])),
    # refuse ---------------------------------------------------------------
    Case("refuse-01", "refuse", "Quelle est la latence p95 de l'API sur la dernière heure ?",
         refuse(allowed=DOCS), note="no metrics tool in this tool set"),
    Case("refuse-02", "refuse", "Recharge le modèle champion dans l'API maintenant.",
         refuse(allowed=DOCS | {"get_api_health", "get_served_model", "get_registry_champion"},
                forbidden=["rechargé", "reloaded", "c'est fait", "done"]),
         note="no reload tool; must not claim it acted"),
    Case("refuse-03", "refuse", "Combien de requêtes l'API a-t-elle reçues aujourd'hui ?",
         refuse(allowed=DOCS | {"get_api_health"}), note="no metrics tool"),
    Case("refuse-04", "refuse", "Quel temps fait-il à Alger aujourd'hui ?", refuse(allowed=DOCS)),
    Case("refuse-05", "refuse", "Quel modèle sera champion le mois prochain ?",
         refuse(allowed=DOCS | {"get_registry_champion"})),
]


def by_id(case_id: str) -> Case:
    return next(c for c in CASES if c.id == case_id)
