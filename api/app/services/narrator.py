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
    management_questions: list[str] = field(default_factory=list)
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
    digest=None,
) -> NarrationResult:
    """Returns narratives plus timing/token metadata for telemetry.

    When a ``digest`` is supplied, the model also synthesizes an executive
    summary over the full dataset (returned under the ``__executive__`` key),
    so the LLM acts as the analyst rather than only rewording rule output.
    """
    if settings.ribet_narration.lower() != "on" or not settings.openai_api_key:
        return NarrationResult(skipped=True)

    digest_has_content = digest is not None and (
        getattr(digest, "ar_total", 0) > 0
        or getattr(digest, "ar_invoice_count", 0) > 0
        or getattr(digest, "ap_total", 0) > 0
        or getattr(digest, "vendor_count", 0) > 0
        or getattr(digest, "gl_txn_count", 0) > 0
        or getattr(digest, "inventory_item_count", 0) > 0
    )

    ranked = sorted(
        findings,
        key=lambda f: SEVERITY_RANK.get(f.severity, 0),
        reverse=True,
    )[:max_findings]

    digest_only = not ranked and digest_has_content

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
        "You are an operational analyst for an SMB manufacturer, writing for the controller. "
        "You are given a full data digest (AR/AP/GL/inventory aggregates and top-N breakdowns) "
        "plus deterministic findings. Reason over the digest numbers directly. "
    )
    if digest_only:
        system += (
            "There are no rule findings this period. Write a 3-5 sentence executive summary "
            "synthesizing the biggest dollar exposures and operational signals across the digest, "
            "quantifying each. Highlight what looks normal vs what warrants monitoring. "
            "Then list 2-4 short, specific questions management should answer. "
            "Return JSON: "
            '{"executive_summary":"...","management_questions":["..."],"narratives":[]}'
        )
    else:
        system += (
            "For each finding, write an 80-120 word narrative citing specific numbers and one concrete "
            "recommendation. Also write a 3-5 sentence executive summary that synthesizes the biggest "
            "dollar exposures and risks across the whole digest (not just the findings), quantifying each. "
            "Then list 2-4 short, specific questions management should answer to resolve uncertainty. "
            "Use ONLY numbers present in the provided data; do not invent figures or unsupported findings; "
            "if a conclusion is uncertain, phrase it as a management question. Return JSON: "
            '{"executive_summary":"...","management_questions":["..."],'
            '"narratives":[{"fingerprint":"...","narrative":"...","recommendation":"..."}]}'
        )
    user = json.dumps(
        {
            "org": org_name,
            "context": context_lines,
            "digest": digest.to_dict() if digest is not None else None,
            "findings": payload,
        },
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
    exec_summary = data.get("executive_summary")
    if isinstance(exec_summary, str) and exec_summary.strip():
        out["__executive__"] = {"narrative": exec_summary.strip(), "recommendation": ""}

    questions = [
        q.strip()
        for q in (data.get("management_questions") or [])
        if isinstance(q, str) and q.strip()
    ]

    logger.info(
        "narration_ok duration_ms=%s model=%s tokens=%s findings=%s",
        duration_ms,
        model,
        usage,
        len(out),
    )
    return NarrationResult(
        narratives=out,
        management_questions=questions,
        duration_ms=duration_ms,
        model_name=model,
        token_usage=usage,
    )
