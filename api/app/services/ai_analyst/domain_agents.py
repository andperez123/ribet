from __future__ import annotations

"""Parallel domain sub-agents."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.schemas.evidence_pack import EvidencePack
from app.services.ai_analyst.client import call_openai_json, pack_to_json
from app.services.ai_analyst.prompts import (
    CONTROLLER_SYSTEM,
    DATA_QUALITY_SYSTEM,
    INVENTORY_SYSTEM,
)


def _run_domain_agent(system: str, pack: EvidencePack, focus: str) -> dict[str, Any]:
    user = pack_to_json(pack) + f"\n\nFocus exclusively on: {focus}"
    data, _, _ = call_openai_json(system, user)
    return data


def run_domain_agents(pack: EvidencePack) -> dict[str, dict[str, Any]]:
    tasks = {
        "controller": (CONTROLLER_SYSTEM, "AR, AP, cash timing, customer and vendor concentration"),
        "inventory": (INVENTORY_SYSTEM, "inventory orphans, zero stock, negative quantities"),
        "data_quality": (DATA_QUALITY_SYSTEM, "mapping warnings, data gaps, upload quality"),
    }
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(_run_domain_agent, system, pack, focus): name
            for name, (system, focus) in tasks.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            results[name] = future.result()
    return results
