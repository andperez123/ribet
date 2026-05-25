from __future__ import annotations

"""Batched OpenAI narration for operational findings."""

import json
import logging

from app.config import settings
from app.services.rules.runner import RuleFinding
from app.services.transforms.snapshot import OperationalSnapshot

logger = logging.getLogger("ribet.narrator")

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def narrate_findings_batch(
    findings: list[RuleFinding],
    org_name: str,
    snapshot: OperationalSnapshot | None = None,
    prior: OperationalSnapshot | None = None,
    max_findings: int = 15,
) -> dict[str, dict[str, str]]:
    """Returns map fingerprint -> {narrative, recommendation}."""
    if settings.ribet_narration.lower() != "on" or not settings.openai_api_key:
        return {}

    ranked = sorted(
        findings,
        key=lambda f: SEVERITY_RANK.get(f.severity, 0),
        reverse=True,
    )[:max_findings]

    payload = []
    for i, f in enumerate(ranked):
        payload.append(
            {
                "idx": i,
                "fingerprint": f.fingerprint,
                "finding_type": f.finding_type,
                "title": f.title,
                "detail": f.detail,
                "severity": f.severity,
                "business_impact": f.business_impact,
                "department": f.department,
            }
        )

    context_lines = []
    if snapshot:
        context_lines.append(
            f"Current period {snapshot.period}: health {snapshot.health_score}, "
            f"AR>90 {snapshot.ar_over_90_pct}%, vendor concentration {snapshot.vendor_concentration}%."
        )
    if prior and snapshot:
        context_lines.append(
            f"Prior period {prior.period}: health {prior.health_score}, "
            f"AR>90 {prior.ar_over_90_pct}%."
        )

    system = (
        "You are an operational analyst writing for an SMB manufacturing controller. "
        "For each finding, write an 80-120 word narrative citing numbers from the detail, "
        "and one concrete recommendation. Return JSON: "
        '{"narratives":[{"fingerprint":"...","narrative":"...","recommendation":"..."}]}'
    )
    user = json.dumps(
        {"org": org_name, "context": context_lines, "findings": payload},
        indent=0,
    )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        out: dict[str, dict[str, str]] = {}
        for item in data.get("narratives", []):
            fp = item.get("fingerprint")
            if fp:
                out[fp] = {
                    "narrative": item.get("narrative", ""),
                    "recommendation": item.get("recommendation", ""),
                }
        return out
    except Exception as e:
        logger.warning("narration_failed error=%s", e)
        return {}
