"""Tool = business card for the model + validated executor for our side.

Security boundary: `ToolRegistry.execute` is the ONLY place a model-generated
ToolCall turns into real work. Everything the model produced (tool name, arguments)
is treated as untrusted input:
  1. unknown tool name        -> error result, nothing runs;
  2. arguments fail the schema -> error result (Pydantic message), nothing runs;
  3. mutating tool             -> a human confirms first, or it is refused.
Errors go BACK to the model as `is_error` observations so it can correct itself,
instead of crashing the loop.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from ..llm.types import ToolCall, ToolResultMessage, ToolSpec


class NoArgs(BaseModel):
    """Explicit 'this tool takes nothing' - still validated (extra keys rejected)."""
    model_config = {"extra": "forbid"}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    run: Callable[[BaseModel], dict[str, Any]]
    mutating: bool = False  # True -> human-in-the-loop before execution

    def spec(self) -> ToolSpec:
        schema = self.args_model.model_json_schema()
        # Pydantic adds class titles and the class docstring; for the model that is
        # noise (tokens) and can even contradict the tool description. Strip it.
        schema.pop("title", None)
        schema.pop("description", None)
        for prop in schema.get("properties", {}).values():
            prop.pop("title", None)
        return ToolSpec(name=self.name, description=self.description, parameters=schema)


ConfirmFn = Callable[[Tool, BaseModel], bool]


class ToolRegistry:
    def __init__(self, tools: list[Tool], confirm: ConfirmFn | None = None):
        self._tools = {t.name: t for t in tools}
        self._confirm = confirm

    def specs(self) -> list[ToolSpec]:
        return [t.spec() for t in self._tools.values()]

    def execute(self, call: ToolCall) -> ToolResultMessage:
        tool = self._tools.get(call.name)
        if tool is None:
            return self._error(call, f"Unknown tool '{call.name}'. "
                                     f"Available: {sorted(self._tools)}")
        try:
            args = tool.args_model.model_validate(call.arguments)
        except ValidationError as exc:
            # The model sees exactly which field is wrong and can retry.
            return self._error(call, f"Invalid arguments: {exc.errors(include_url=False)}")
        if tool.mutating:
            if self._confirm is None or not self._confirm(tool, args):
                return self._error(call, "Action refused: this tool changes system state "
                                         "and no human confirmation was given.")
        try:
            result = tool.run(args)
        except Exception as exc:  # network, 503, timeouts: the model must know, not crash
            return self._error(call, f"{type(exc).__name__}: {exc}")
        return ToolResultMessage(call_id=call.id, name=call.name,
                                 content=json.dumps(result, ensure_ascii=False))

    @staticmethod
    def _error(call: ToolCall, message: str) -> ToolResultMessage:
        return ToolResultMessage(call_id=call.id, name=call.name,
                                 content=message, is_error=True)
