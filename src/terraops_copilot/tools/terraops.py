"""Sprint 1 tool set: 3 tools, all read-only.

The descriptions are the most important code in this sprint. Rules used:
- say WHEN to use the tool (the user intent), not just what it returns;
- say when NOT to use it, naming the neighbouring tool (health vs monitoring,
  served model vs registry champion);
- name the fields the model will get back, so it can plan the answer.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..client.terraops_api import TerraOpsClient
from .base import NoArgs, Tool

REGISTRY_MODEL = "terraops-eurosat"


class RegistryArgs(BaseModel):
    model_config = {"extra": "forbid"}
    alias: Literal["champion"] = Field(
        default="champion",
        description="Registry alias to resolve. Only 'champion' exists today "
                    "(the version approved by the promotion gate).")


def build_tools(client: TerraOpsClient) -> list[Tool]:
    return [
        Tool(
            name="get_api_health",
            description=(
                "Check whether the TerraOps serving API is up and whether a model is "
                "loaded in memory. Use for questions like 'is the API running?', "
                "'is the service healthy?', 'can I send predictions?'. Returns "
                "status, model_loaded (bool) and model_version. Do NOT use it to "
                "learn which model is served (use get_served_model) or whether the "
                "monitoring/prediction log works (that is a different question)."
            ),
            args_model=NoArgs,
            run=lambda _a: client.health(),
        ),
        Tool(
            name="get_served_model",
            description=(
                "Describe the model CURRENTLY LOADED in the serving API: registry "
                "name, alias, version number, the 10 EuroSAT classes it predicts, "
                "input image size, device (cpu/gpu) and load time. Use for 'which "
                "model/version is serving right now?', 'what classes can it "
                "recognise?'. This is the live API view; it can lag behind the "
                "registry if a new champion was promoted but the API was not "
                "reloaded - compare with get_registry_champion for that."
            ),
            args_model=NoArgs,
            run=lambda _a: client.model_info(),
        ),
        Tool(
            name="get_registry_champion",
            description=(
                "Look up, in the MLflow Model Registry, which version of "
                f"'{REGISTRY_MODEL}' holds the given alias (default 'champion' = the "
                "version approved by the promotion gate). Use for 'what is the "
                "current champion model?', 'which version won the gate?', 'what "
                "accuracy did the champion get on the frozen set?'. Returns version, "
                "run_id, status and the gate tags (gate_accuracy, gate_ms_per_image, "
                "gate_result, gate_data_hash). This is the registry's source of "
                "truth, not necessarily what the API is serving right now."
            ),
            args_model=RegistryArgs,
            run=lambda a: _compact_version(client.registry_model_by_alias(REGISTRY_MODEL, a.alias)),
        ),
    ]


def _compact_version(mv: dict) -> dict:
    """Keep only what the model needs: fewer tokens, no timestamps to misread."""
    return {
        "name": mv.get("name"),
        "version": mv.get("version"),
        "aliases": mv.get("aliases", []),
        "status": mv.get("status"),
        "run_id": mv.get("run_id"),
        "tags": {t["key"]: t["value"] for t in mv.get("tags", [])},
    }
