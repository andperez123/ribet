from __future__ import annotations

"""Batched OpenAI narration for operational findings."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field

from app.config import settings
from app.services.rules.runner import RuleFinding
from app.services.transforms.snapshot import OperationalSnapshot

logger = logging.getLogger("ribet.narrator")

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


@dataclass
class NarrationResult:
    narratives: dict[str, dict[str, str]] = field(default_factory=dict)
    failed: bool = False
    skipped: bool = False
    duration_ms: int = 0
    model_name: str | None = None
    token_usage: dict[str, int] | None = None
    error_type: str | None = None


def _call_openai(
    system: str,
    user: str,
) -> tuple[dict, dict[str, int] | None, str]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.openai_model
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    usage = None
    if resp.usage:
        usage = {
            "prompt_tokens": resp.usage.prompt_tokens or 0,
            "completion_tokens": resp.usage.completion_tokens or 0,
            "total_tokens": resp.usage.total_tokens or 0,
        }
    raw = resp.choices[0].message.content or "{}"
    return json.loads(raw), usage, model


def narrate_findings_batch(
    findings: list[RuleFinding],
    org_name: str,
    snapshot: OperationalSnapshot | None = None,
    prior: OperationalSnapshot | None = None,
    max_findings: int = 15,
) -> NarrationResult:
    """Returns narratives plus timing/token metadata for telemetry."""
    if settings.ribet_narration.lower() != "on" or not settings.openai_api_key:
        return NarrationResult(skipped=True)

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

    import time

    start = time.perf_counter()
    timeout = settings.ribet_narration_timeout_seconds

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_call_openai, system, user)
            data, usage, model = future.result(timeout=timeout)
    except FuturesTimeoutError:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.warning("narration_failed error=timeout duration_ms=%s", duration_ms)
        return NarrationResult(
            failed=True,
            duration_ms=duration_ms,
            model_name=settings.openai_model,
            error_type="TimeoutError",
        )
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(
            "narration_failed error=%s duration_ms=%s", e, duration_ms
        )
        return NarrationResult(
            failed=True,
            duration_ms=duration_ms,
            model_name=settings.openai_model,
            error_type=type(e).__name__,
        )

    duration_ms = int((time.perf_counter() - start) * 1000)
    out: dict[str, dict[str, str]] = {}
    for item in data.get("narratives", []):
        fp = item.get("fingerprint")
        if fp:
            out[fp] = {
                "narrative": item.get("narrative", ""),
                "recommendation": item.get("recommendation", ""),
            }

    logger.info(
        "narration_ok duration_ms=%s model=%s tokens=%s findings=%s",
        duration_ms,
        model,
        usage,
        len(out),
    )
    return NarrationResult(
        narratives=out,
        duration_ms=duration_ms,
        model_name=model,
        token_usage=usage,
    )
