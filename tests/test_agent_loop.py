"""The loop, provider-free: think -> act -> observe -> answer, with guard rails."""
from fake_llm import FakeLLM, text_reply, tool_reply

from terraops_copilot.agent.loop import Agent
from terraops_copilot.llm.types import AssistantMessage, ToolResultMessage, UserMessage
from terraops_copilot.tools.base import NoArgs, Tool, ToolRegistry


def registry():
    return ToolRegistry([Tool("get_x", "x", NoArgs, lambda a: {"x": 42})])


def test_tool_call_then_answer():
    llm = FakeLLM([tool_reply("get_x"), text_reply("x vaut 42")])
    result = Agent(llm, registry()).run("x ?")
    assert result.answer == "x vaut 42"
    assert result.tools_called == ["get_x"]
    # Second model call saw: user, assistant(tool call), tool result.
    _, msgs, _ = llm.calls[1]
    assert [type(m) for m in msgs] == [UserMessage, AssistantMessage, ToolResultMessage]
    assert '"x": 42' in msgs[2].content


def test_no_tool_needed_answers_directly():
    llm = FakeLLM([text_reply("Je ne peux pas faire ça avec mes outils.")])
    result = Agent(llm, registry()).run("commande une pizza")
    assert result.tools_called == [] and "ne peux pas" in result.answer


def test_error_result_is_fed_back_to_model():
    llm = FakeLLM([tool_reply("nope"), text_reply("cet outil n'existe pas")])
    result = Agent(llm, registry()).run("?")
    assert result.steps[0].results[0].is_error
    assert result.answer == "cet outil n'existe pas"


def test_max_steps_stops_a_runaway_model():
    llm = FakeLLM([tool_reply("get_x", call_id=str(i)) for i in range(10)]
                  + [text_reply("final")])
    result = Agent(llm, registry(), max_steps=3).run("?")
    assert len(result.tools_called) == 3
    # The closing call must offer NO tools, so the model cannot keep going.
    assert llm.calls[-1][2] == []
