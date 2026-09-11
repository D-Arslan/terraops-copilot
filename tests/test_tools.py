"""The security boundary: nothing runs unless name and arguments are valid."""
import json

from pydantic import BaseModel

from terraops_copilot.llm.types import ToolCall
from terraops_copilot.tools.base import NoArgs, Tool, ToolRegistry


class EchoArgs(BaseModel):
    model_config = {"extra": "forbid"}
    n: int


def make_registry(calls: list, confirm=None):
    return ToolRegistry([
        Tool("echo", "echo n", EchoArgs, lambda a: {"n": a.n}),
        Tool("noargs", "nothing", NoArgs, lambda a: {"ok": True}),
        Tool("danger", "mutates", NoArgs, lambda a: calls.append("ran") or {"done": True},
             mutating=True),
    ], confirm=confirm)


def test_valid_call_runs_and_returns_json():
    reg = make_registry([])
    res = reg.execute(ToolCall("1", "echo", {"n": 3}))
    assert not res.is_error and json.loads(res.content) == {"n": 3}


def test_unknown_tool_is_refused_not_raised():
    res = make_registry([]).execute(ToolCall("1", "rm_rf", {}))
    assert res.is_error and "Unknown tool" in res.content


def test_wrong_type_is_rejected_before_execution():
    res = make_registry([]).execute(ToolCall("1", "echo", {"n": "three"}))
    assert res.is_error and "Invalid arguments" in res.content


def test_extra_field_is_rejected():
    res = make_registry([]).execute(ToolCall("1", "noargs", {"path": "/etc/passwd"}))
    assert res.is_error


def test_mutating_tool_refused_without_confirmation():
    ran: list = []
    res = make_registry(ran).execute(ToolCall("1", "danger", {}))
    assert res.is_error and ran == []


def test_mutating_tool_runs_when_confirmed():
    ran: list = []
    res = make_registry(ran, confirm=lambda t, a: True).execute(ToolCall("1", "danger", {}))
    assert not res.is_error and ran == ["ran"]


def test_executor_exception_becomes_error_result():
    reg = ToolRegistry([Tool("boom", "x", NoArgs, lambda a: 1 / 0)])
    res = reg.execute(ToolCall("1", "boom", {}))
    assert res.is_error and "ZeroDivisionError" in res.content


def test_spec_is_json_schema_without_title():
    spec = Tool("echo", "echo n", EchoArgs, lambda a: {}).spec()
    assert spec.parameters["type"] == "object"
    assert "n" in spec.parameters["properties"] and "title" not in spec.parameters


def test_salvage_text_tool_calls_from_lmstudio_markup():
    from terraops_copilot.llm.openai_compat_client import salvage_text_tool_calls
    text = ('Je consulte la documentation, car la question porte sur un concept.  '
            '[search_documentation] {"query": "seuils du gate", "k": 4} [END_TOOL_REQUEST]')
    remaining, calls = salvage_text_tool_calls(text)
    assert remaining == "Je consulte la documentation, car la question porte sur un concept."
    assert [(c.name, c.arguments) for c in calls] == [("search_documentation", {"query": "seuils du gate", "k": 4})]
    remaining, calls = salvage_text_tool_calls('[TOOL_REQUEST] {"name": "get_registry_champion", "arguments": {}} [END_TOOL_REQUEST]')
    assert remaining is None and calls[0].name == "get_registry_champion" and calls[0].arguments == {}
    remaining, calls = salvage_text_tool_calls("[bad] {not json} [END_TOOL_REQUEST]")
    assert calls == [] and "[bad]" in remaining
