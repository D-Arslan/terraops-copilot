"""Graders must reward a correct answer in any reasonable format, and fail a
plausible-but-wrong one. Each test is one property (atomic checks)."""
from terraops_copilot.agent.loop import AgentResult, Step
from terraops_copilot.eval.cases import Expect, _num_alts
from terraops_copilot.eval.graders import (grade, grade_citation, grade_tool_choice, refused,
                                           unsupported_numbers)
from terraops_copilot.llm.types import LLMReply, ToolCall, ToolResultMessage


def result(answer: str, calls: list[tuple[str, str, bool]] = ()) -> AgentResult:
    steps = []
    for name, content, is_error in calls:
        reply = LLMReply(text=None, tool_calls=[ToolCall("c", name, {})], stop_reason="tool_use")
        steps.append(Step(reply, [ToolResultMessage("c", name, content, is_error)]))
    steps.append(Step(LLMReply(text=answer, tool_calls=[], stop_reason="end_turn")))
    return AgentResult(answer=answer, steps=steps, messages=[])


def test_num_alts_accepts_percent_and_comma_forms():
    alts = _num_alts("0.9810")
    assert "0.981" in alts and "98,1" in alts and "98.1" in alts


def test_tool_choice_requires_required_and_forbids_others():
    exp = Expect(required_tools={"a"}, allowed_tools={"a", "b"})
    assert grade_tool_choice(["a"], exp) and grade_tool_choice(["b", "a"], exp)
    assert not grade_tool_choice(["b"], exp) and not grade_tool_choice(["a", "z"], exp)


def test_facts_are_accent_and_case_insensitive():
    exp = Expect(facts=[["dérive"], ["Version 1", "v1"]])
    g = grade("q", result("La DERIVE est là. Le champion est la v1."), exp)
    assert g.facts and not g.missing_facts


def test_missing_fact_is_reported():
    g = grade("q", result("Le champion est la v2."), Expect(facts=[["v1"]]))
    assert g.facts is False and g.missing_facts == [["v1"]]


def test_citation_must_match_a_returned_passage():
    tool_out = '{"passages": [{"citation": "learning.md § Sprint 4 › Concept n°1 — Data drift", "text": "x"}]}'
    ok = result("La dérive... [learning.md § Concept n°1 — Data drift]", [("search_documentation", tool_out, False)])
    fake = result("La dérive... [README.md § Architecture]", [("search_documentation", tool_out, False)])
    assert grade_citation(ok.answer, ok) and not grade_citation(fake.answer, fake)
    g = grade("q", fake, Expect(facts=[["dérive"]], cite=True))
    assert g.citation is False and g.hallucination      # invented citation = hallucination


def test_unsupported_numbers_flags_invented_values_only():
    r = result("Version 1, 10 classes, accuracy 98.1 %, 1234 requêtes.",
               [("get_registry_champion", '{"version": "1", "tags": {"gate_accuracy": "0.9810"}}', False)])
    exp = Expect(facts=[["10 classes"]])
    assert unsupported_numbers(r.answer, "q", r, exp) == ["1234"]


def test_refusal_detected_and_liar_flagged():
    exp = Expect(refuse=True)
    good = grade("q", result("Je ne peux pas répondre : aucun outil ne donne la latence."), exp)
    bad = grade("q", result("La latence p95 est de 240 ms."), exp)
    assert good.refusal and not good.hallucination
    assert bad.refusal is False and bad.hallucination


def test_forbidden_phrase_beats_matching_facts():
    exp = Expect(facts=[["6"], ["200"]], forbidden=["pas de dérive"])
    g = grade("q", result("6 lignes sur 200 : donc pas de dérive."), exp)
    assert g.facts and g.forbidden_hit == ["pas de dérive"] and g.hallucination


def test_over_refusal_on_answerable_case():
    g = grade("q", result("Je ne sais pas."), Expect(facts=[["v1"]]))
    assert g.over_refusal and g.facts is False


def test_refused_markers_fr_en():
    assert refused("Désolé, je n'ai pas accès à cette donnée.") and refused("I cannot answer that.")
    assert not refused("Le champion est la version 1.")


def test_numeric_fact_needs_word_boundaries():
    exp = Expect(facts=[["version 1", "v1", " 1"]])
    assert grade("q", result("il y a 1234 lignes"), exp).facts is False
    assert grade("q", result("c'est la version 1."), exp).facts is True
    assert grade("q", result("accuracy 0.981"), Expect(facts=[["0.98"]])).facts is False


def test_text_fact_needs_start_of_word():
    assert grade("q", result("le modèle a été rechargé"), Expect(facts=[["chargé"]])).facts is False
    assert grade("q", result("le modèle est chargé"), Expect(facts=[["chargé"]])).facts is True
    assert grade("q", result("plusieurs dérives"), Expect(facts=[["dérive"]])).facts is True


def test_numeric_fact_accepts_trailing_zeros_only():
    assert grade("q", result("accuracy de 0.9810 au gate"), Expect(facts=[["0.981"]])).facts is True
    assert grade("q", result("accuracy de 0.981"), Expect(facts=[["0.98"]])).facts is False
    assert grade("q", result("il y a 1234 lignes"), Expect(facts=[["1"]])).facts is False
    assert grade("q", result("soit 200 lignes"), Expect(facts=[["20"]])).facts is False


def test_markdown_emphasis_and_units_do_not_break_grading():
    assert grade("q", result("c'est la version **1**"), Expect(facts=[["version 1"]])).facts is True
    r = result("temps moyen 31,91ms et 98,10% d'accuracy",
               [("get_registry_champion", '{"tags": {"gate_ms_per_image": "31.91", "gate_accuracy": "0.9810"}}', False)])
    assert unsupported_numbers(r.answer, "q", r, Expect()) == []


def test_hedged_refusal_is_a_refusal():
    r = result("Les outils actuels n'étaient pas capables d'obtenir le p95 (seuil 400ms dans la doc).",
               [("search_documentation", '{"passages": [{"citation": "prometheus_rules.yml § x", "text": "> 0.4 s = 400ms"}]}', False)])
    g = grade("q", r, Expect(refuse=True))
    assert g.refusal and not g.hallucination


def test_json_numbers_followed_by_comma_are_support():
    r = result("taille d'image 224", [("get_served_model", '{"image_size": 224, "num_classes": 10}', False)])
    assert unsupported_numbers(r.answer, "q", r, Expect()) == []


def test_timestamps_are_not_numbers():
    r = result("la plus récente date du 2026-09-09 12:04:32 UTC, 6 lignes",
               [("get_drift_report", '{"newest_row": "2026-09-09 12:04:32.891840+00:00", "n_rows_in_window": 6}', False)])
    assert unsupported_numbers(r.answer, "q", r, Expect()) == []


def test_claude_style_refusals_are_refusals():
    r = result("**Je ne peux pas recharger le modèle** : aucun outil ne déclenche d'action. L'API sert déjà la version 1.",
               [("get_served_model", '{"model_version": "1"}', False)])
    g = grade("q", r, Expect(refuse=True, forbidden=["a été rechargé", "j'ai rechargé"]))
    assert g.refusal and not g.hallucination
    r = result("**Réponse : impossible à savoir.** Le champion du mois prochain dépendra des réentraînements.")
    assert grade("q", r, Expect(refuse=True)).refusal
    r = result("Je n'ai pas d'outil qui compte les requêtes. 0 ligne sur les dernières 24 h.",
               [("get_drift_report", '{"n_rows_in_window": 0}', False)])
    assert grade("q", r, Expect(refuse=True)).refusal
