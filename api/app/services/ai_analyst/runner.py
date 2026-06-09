from __future__ import annotations

"""Orchestrate multi-agent AI analyst over Evidence Pack."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models import ReportNarrative
from app.schemas.analyst_output import PROMPT_VERSION, AnalystOutput
from app.schemas.evidence_pack import EvidencePack
from app.services.ai_analyst.domain_agents import run_domain_agents
from app.services.ai_analyst.executive import run_executive_agent
from app.services.ai_analyst.fallback import build_deterministic_analyst_output
from app.services.ai_analyst.verification import verify_ai_output

logger = logging.getLogger("ribet.ai_analyst")


@dataclass
class AnalystResult:
    output: AnalystOutput | None = None
    skipped: bool = False
    failed: bool = False
    used_fallback: bool = False
    verification_status: str = "skipped"
    verification_failures: list[str] = field(default_factory=list)
    duration_ms: int = 0
    model_name: str | None = None
    token_usage: dict[str, int] | None = None
    error_type: str | None = None


def run_ai_analyst(pack: EvidencePack) -> AnalystResult:
    """Run domain agents in parallel, executive synthesizer, verify, regenerate once, fallback."""
    if settings.ribet_narration.lower() != "on" or not settings.openai_api_key:
        return AnalystResult(skipped=True, verification_status="skipped")

    if not pack.agent_ready:
        return AnalystResult(skipped=True, verification_status="skipped")

    start = time.perf_counter()
    timeout = settings.ribet_narration_timeout_seconds

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_pipeline, pack)
            output, usage, model, failures, used_fallback = future.result(timeout=timeout)
    except FuturesTimeoutError:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.warning("ai_analyst_timeout duration_ms=%s", duration_ms)
        fallback = build_deterministic_analyst_output(pack)
        return AnalystResult(
            output=fallback,
            used_fallback=True,
            verification_status="fallback",
            duration_ms=duration_ms,
            error_type="TimeoutError",
        )
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.warning("ai_analyst_failed error=%s duration_ms=%s", e, duration_ms)
        fallback = build_deterministic_analyst_output(pack)
        return AnalystResult(
            output=fallback,
            used_fallback=True,
            verification_status="fallback",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
        )

    duration_ms = int((time.perf_counter() - start) * 1000)
    status = "fallback" if used_fallback else ("passed" if not failures else "failed")
    if used_fallback:
        logger.info("ai_analyst_fallback duration_ms=%s", duration_ms)
    else:
        logger.info("ai_analyst_ok duration_ms=%s model=%s", duration_ms, model)

    return AnalystResult(
        output=output,
        used_fallback=used_fallback,
        verification_status=status,
        verification_failures=failures,
        duration_ms=duration_ms,
        model_name=model,
        token_usage=usage,
    )


def _run_pipeline(pack: EvidencePack) -> tuple[AnalystOutput, dict | None, str | None, list[str], bool]:
    domain_outputs = run_domain_agents(pack)
    output, usage, model = run_executive_agent(pack, domain_outputs)
    result = verify_ai_output(pack, output)
    if result.passed:
        return output, usage, model, [], False

    logger.warning("ai_analyst_verify_failed failures=%s", result.failures)
    output2, usage2, model2 = run_executive_agent(pack, domain_outputs, result.failures)
    result2 = verify_ai_output(pack, output2)
    if result2.passed:
        merged_usage = usage
        if usage2 and merged_usage:
            for k, v in usage2.items():
                merged_usage[k] = merged_usage.get(k, 0) + v
        elif usage2:
            merged_usage = usage2
        return output2, merged_usage, model2, [], False

    fallback = build_deterministic_analyst_output(pack)
    return fallback, usage, model, result2.failures, True


def persist_report_narrative(
    db: Session,
    report_id: UUID,
    org_id: UUID,
    result: AnalystResult,
) -> ReportNarrative | None:
    if result.skipped or result.output is None:
        return None

    existing = db.query(ReportNarrative).filter(ReportNarrative.report_id == report_id).first()
    row_data = {
        "output": result.output.model_dump(mode="json"),
        "schema_version": result.output.schema_version,
        "prompt_version": PROMPT_VERSION,
        "verification_status": result.verification_status,
        "verification_failures": result.verification_failures or None,
        "model_name": result.model_name,
        "duration_ms": result.duration_ms,
        "token_usage": result.token_usage,
        "source": result.output.source,
    }
    if existing:
        for k, v in row_data.items():
            setattr(existing, k, v)
        db.flush()
        return existing

    row = ReportNarrative(report_id=report_id, org_id=org_id, **row_data)
    db.add(row)
    db.flush()
    return row


def get_analyst_output_for_report(db: Session, report_id: UUID) -> dict | None:
    row = (
        db.query(ReportNarrative)
        .filter(ReportNarrative.report_id == report_id)
        .first()
    )
    return row.output if row else None