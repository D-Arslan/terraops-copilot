"""The agentic loop (ReAct-style): think -> act -> observe -> repeat -> answer.

Why a loop and not one call: the model cannot know the answer before observing the
tool result, and it may need a second tool after reading the first (e.g. compare the
served version with the registry champion). Each iteration is a full new request
carrying the whole history, so the model 'remembers' only what we append.

Guard rails owned by this loop (not by the model):
- max_steps: an LLM that keeps calling tools would otherwise loop forever/spend money;
- every ToolCall goes through ToolRegistry.execute (validation, confirmation);
- the system prompt tells the model to refuse rather than guess when no tool fits.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..llm.base import LLMClient
from ..llm.types import (AssistantMessage, LLMReply, Message, ToolResultMessage,
                         UserMessage)
from ..tools.base import ToolRegistry

SYSTEM_PROMPT = """You are TerraOps Copilot, an operations assistant for the TerraOps
MLOps platform (a EuroSAT land-use classifier served by FastAPI, with an MLflow model
registry). You answer in the user's language (usually French).

Rules:
1. Never state a fact about the running system (versions, status, metrics, drift,
   classes, accuracies) from memory. Get it from a live tool, then quote the value.
2. Two kinds of questions, two kinds of tools. CURRENT STATE ("is there drift this
   week?", "which version is served?") -> live tools. CONCEPTS and design ("what is
   drift?", "how does promotion work?") -> search_documentation. A question can need
   both ("is there drift, and what does that mean?").
3. When you answer from documentation passages, cite each one as [source § section]
   right after the claim it supports, and only claim what the passages say.
4. If no available tool can answer, or the documentation has no relevant passage,
   say so clearly and name what would be needed. Do not guess, do not fabricate.
5. Prefer one tool call when one is enough. Call several only when the question
   requires combining them.
6. When a tool returns an error or an inconclusive result, report it as such
   ("not enough data" is not "no drift") instead of retrying endlessly.
7. Keep answers short and factual; mention which tool the value came from."""


@dataclass
class Step:
    reply: LLMReply
    results: list[ToolResultMessage] = field(default_factory=list)


@dataclass
class AgentResult:
    answer: str
    steps: list[Step]
    messages: list[Message]

    @property
    def tools_called(self) -> list[str]:
        return [c.name for s in self.steps for c in s.reply.tool_calls]


class Agent:
    def __init__(self, llm: LLMClient, registry: ToolRegistry, max_steps: int = 5,
                 system_prompt: str = SYSTEM_PROMPT):
        self.llm = llm
        self.registry = registry
        self.max_steps = max_steps
        self.system_prompt = system_prompt

    def run(self, question: str) -> AgentResult:
        messages: list[Message] = [UserMessage(question)]
        steps: list[Step] = []
        specs = self.registry.specs()

        for _ in range(self.max_steps):
            reply = self.llm.chat(self.system_prompt, messages, specs)   # THINK
            messages.append(AssistantMessage(reply.text, reply.tool_calls))
            step = Step(reply)
            steps.append(step)

            if not reply.wants_tools:                                     # ANSWER
                return AgentResult(answer=reply.text or "", steps=steps, messages=messages)

            for call in reply.tool_calls:                                 # ACT
                result = self.registry.execute(call)                      # (validated)
                step.results.append(result)
                messages.append(result)                                   # OBSERVE

        # Budget exhausted: ask for a final answer WITHOUT tools rather than fail silently.
        reply = self.llm.chat(
            self.system_prompt + "\nYou have used all your tool calls. Answer now with "
            "what you have, or say what is missing.", messages, tools=[])
        # Defensive: even if the model still emits a tool call, it is NOT executed.
        final = LLMReply(text=reply.text, tool_calls=[], stop_reason=reply.stop_reason,
                         usage=reply.usage)
        messages.append(AssistantMessage(final.text, []))
        steps.append(Step(final))
        return AgentResult(answer=final.text or "", steps=steps, messages=messages)
