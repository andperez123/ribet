from __future__ import annotations

"""Verify AI analyst output against the Evidence Pack."""

import re
from typing import Any

from app.schemas.analyst_output import AnalystOutput, METRIC_KEY_VOCABULARY, VerifyResult
from app.schemas.evidence_pack import EvidencePack

_NUMBER_RE = re.compile(
    r"(?<!\w)(?:\$?\d{1,3}(?:,\d{3})+(?:\.\d+)?|\$?\d+(?:\.\d+)?%?)(?!\w)"
)
_CAUSAL_RE = re.compile(r"\b(because|due to|caused by|as a result of)\b", re.I)


def _normalize_number(raw: str) -> str:
    return raw.replace("$", "").replace(",", "").rstrip("%")


def _collect_allowed_numbers(pack: EvidencePack) -> set[str]:
    allowed: set[str] = set()

    def walk(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, prefix)
        elif isinstance(obj, (int, float)) and obj != 0:
            val = float(obj)
            allowed.add(str(int(val)) if val.is_integer() else f"{val:.2f}".rstrip("0").rstrip("."))
            allowed.add(f"{val:.1f}")

    walk(pack.metrics, "metrics")
    walk(pack.health.model_dump(), "health")
    for finding in pack.findings:
        walk(finding.evidence)

    return allowed


def _extract_numbers_from_text(text: str) -> set[str]:
    return {_normalize_number(m) for m in _NUMBER_RE.findall(text or "") if _normalize_number(m)}


def _all_text_blobs(output: AnalystOutput) -> list[str]:
    texts: list[str] = []
    texts.extend(output.executive_summary)
    texts.extend(output.confidence_notes)
    for risk in output.top_risks:
        texts.extend([risk.title, risk.narrative, risk.recommended_action])
    for item in output.what_changed:
        texts.append(item.narrative)
    for q in output.management_questions:
        texts.extend([q.question, q.context])
    for upload in output.recommended_uploads:
        texts.extend([upload.rationale, upload.upload])
    de = output.dashboard_explanations
    texts.extend([de.ar_risk, de.cash_flow, de.inventory, de.data_quality])
    di = output.domain_insights
    texts.extend([di.controller, di.inventory, di.data_quality])
    for ci in output.conditional_insights:
        texts.append(ci.insight)
    briefing = output.dashboard_briefing
    texts.extend([briefing.headline, briefing.narrative, briefing.focus])
    for takeaway in output.metric_takeaways:
        texts.append(takeaway.takeaway)
    return texts


def all_numbers_traceable(output: AnalystOutput, pack: EvidencePack) -> tuple[bool, list[str]]:
    if output.source == "deterministic_fallback":
        return True, []
    allowed = _collect_allowed_numbers(pack)
    allowed.add(str(pack.health.score))
    allowed.add(str(pack.confidence.legacy_score))
    allowed.add(str(int(round(pack.confidence.normalized_score * 100))))
    for part in pack.period.split("-"):
        allowed.add(part)
    failures: list[str] = []
    for text in _all_text_blobs(output):
        for num in _extract_numbers_from_text(text):
            if num in allowed:
                continue
            if any(num.startswith(a) or a.startswith(num) for a in allowed if len(a) >= 2):
                continue
            failures.append(f"Untraceable number '{num}' in: {text[:80]}...")
    return len(failures) == 0, failures


def all_finding_ids_valid(output: AnalystOutput, pack: EvidencePack) -> tuple[bool, list[str]]:
    valid_ids = {f.finding_id for f in pack.findings if f.finding_id}
    failures: list[str] = []

    def check_ids(ids: list[str], context: str) -> None:
        for fid in ids:
            if fid and fid not in valid_ids:
                failures.append(f"Invalid finding_id '{fid}' in {context}")

    for risk in output.top_risks:
        check_ids(risk.finding_ids, f"top_risk '{risk.title}'")
    for item in output.what_changed:
        check_ids(item.finding_ids, f"what_changed '{item.metric_key}'")
    for q in output.management_questions:
        check_ids(q.finding_ids, "management_question")
    for upload in output.recommended_uploads:
        check_ids(upload.finding_ids, f"recommended_upload '{upload.upload}'")
    for ci in output.conditional_insights:
        check_ids(ci.finding_ids, "conditional_insight")

    return len(failures) == 0, failures


def all_uploads_traceable(output: AnalystOutput, pack: EvidencePack) -> tuple[bool, list[str]]:
    allowed_uploads = {g.upload for g in pack.data_gaps}
    failures = []
    for upload in output.recommended_uploads:
        if upload.upload not in allowed_uploads:
            failures.append(f"Upload '{upload.upload}' not in evidence pack data_gaps")
    return len(failures) == 0, failures


def no_phantom_causality(output: AnalystOutput, pack: EvidencePack) -> tuple[bool, list[str]]:
    if output.source == "deterministic_fallback":
        return True, []
    if len([k for k, v in pack.coverage.domains.items() if v]) >= 3:
        return True, []
    failures = []
    for text in _all_text_blobs(output):
        if _CAUSAL_RE.search(text) and "may" not in text.lower() and "might" not in text.lower():
            failures.append(f"Unsupported causal language: {text[:100]}...")
    return len(failures) == 0, failures


def metric_keys_valid(output: AnalystOutput) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for takeaway in output.metric_takeaways:
        if takeaway.metric_key not in METRIC_KEY_VOCABULARY:
            failures.append(f"Invalid metric_key '{takeaway.metric_key}' in metric_takeaways")
    return len(failures) == 0, failures


def all_metric_finding_ids_valid(output: AnalystOutput, pack: EvidencePack) -> tuple[bool, list[str]]:
    valid_ids = {f.finding_id for f in pack.findings if f.finding_id}
    failures: list[str] = []
    for takeaway in output.metric_takeaways:
        for fid in takeaway.finding_ids:
            if fid and fid not in valid_ids:
                failures.append(f"Invalid finding_id '{fid}' in metric_takeaway '{takeaway.metric_key}'")
    return len(failures) == 0, failures


def confidence_notes_honest(output: AnalystOutput, pack: EvidencePack) -> tuple[bool, list[str]]:
    if not output.confidence_notes:
        return True, []
    notes_text = " ".join(output.confidence_notes).lower()
    if pack.confidence.normalized_score < 0.5:
        if "confidence" not in notes_text and "coverage" not in notes_text:
            return False, ["confidence_notes should reference low coverage/confidence"]
    return True, []


def schema_valid(output: AnalystOutput) -> tuple[bool, list[str]]:
    try:
        AnalystOutput.model_validate(output.model_dump())
        return True, []
    except Exception as e:
        return False, [str(e)]


def verify_ai_output(pack: EvidencePack, output: AnalystOutput) -> VerifyResult:
    checks = {
        "numbers_traceable": all_numbers_traceable(output, pack)[0],
        "finding_ids_valid": all_finding_ids_valid(output, pack)[0],
        "uploads_traceable": all_uploads_traceable(output, pack)[0],
        "no_phantom_causality": no_phantom_causality(output, pack)[0],
        "confidence_notes_honest": confidence_notes_honest(output, pack)[0],
        "schema_valid": schema_valid(output)[0],
        "metric_keys_valid": metric_keys_valid(output)[0],
        "metric_finding_ids_valid": all_metric_finding_ids_valid(output, pack)[0],
    }
    failures: list[str] = []
    for name, fn in (
        ("numbers_traceable", lambda: all_numbers_traceable(output, pack)),
        ("finding_ids_valid", lambda: all_finding_ids_valid(output, pack)),
        ("uploads_traceable", lambda: all_uploads_traceable(output, pack)),
        ("no_phantom_causality", lambda: no_phantom_causality(output, pack)),
        ("confidence_notes_honest", lambda: confidence_notes_honest(output, pack)),
        ("schema_valid", lambda: schema_valid(output)),
        ("metric_keys_valid", lambda: metric_keys_valid(output)),
        ("metric_finding_ids_valid", lambda: all_metric_finding_ids_valid(output, pack)),
    ):
        ok, errs = fn()
        checks[name] = ok
        failures.extend(errs)
    return VerifyResult(passed=all(checks.values()), failures=failures, checks=checks)
