from __future__ import annotations

"""Executive synthesizer agent."""

import json
from typing import Any

from app.schemas.analyst_output import AnalystOutput
from app.schemas.evidence_pack import EvidencePack
from app.services.ai_analyst.client import call_openai_json, pack_to_json
from app.services.ai_analyst.prompts import EXECUTIVE_SYSTEM, REGENERATE_SUFFIX


def run_executive_agent(
    pack: EvidencePack,
    domain_outputs: dict[str, dict[str, Any]],
    verification_failures: list[str] | None = None,
) -> tuple[AnalystOutput, dict[str, int] | None, str]:
    system = EXECUTIVE_SYSTEM
    if verification_failures:
        system += REGENERATE_SUFFIX.format(failures=json.dumps(verification_failures))

    user = json.dumps(
        {
            "evidence_pack": json.loads(pack_to_json(pack)),
            "domain_agent_outputs": domain_outputs,
        },
        indent=0,
    )
    data, usage, model = call_openai_json(system, user)
    domain_insights = data.get("domain_insights") or {}
    if not domain_insights.get("controller"):
        domain_insights["controller"] = (domain_outputs.get("controller") or {}).get("domain_insight", "")
    if not domain_insights.get("inventory"):
        domain_insights["inventory"] = (domain_outputs.get("inventory") or {}).get("domain_insight", "")
    if not domain_insights.get("data_quality"):
        domain_insights["data_quality"] = (domain_outputs.get("data_quality") or {}).get("domain_insight", "")
    if domain_outputs.get("procurement") and not domain_insights.get("procurement"):
        domain_insights["procurement"] = domain_outputs["procurement"].get("domain_insight", "")
    if domain_outputs.get("sales") and not domain_insights.get("sales"):
        domain_insights["sales"] = domain_outputs["sales"].get("domain_insight", "")
    data["domain_insights"] = domain_insights
    output = AnalystOutput.model_validate(data)
    return output, usage, model
