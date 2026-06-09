"""Tests for AI analyst verification and deterministic fallback."""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.analyst_output import AnalystOutput, RecommendedUpload, TopRisk
from app.schemas.evidence_pack import (
    EvidencePack,
    EvidencePackConfidence,
    EvidencePackConfidenceComponents,
    EvidencePackCoverage,
    EvidencePackDataGap,
    EvidencePackHealth,
    EvidencePackHealthComponents,
    EvidencePackMemory,
    EvidencePackTopEntities,
)
from app.services.ai_analyst.fallback import build_deterministic_analyst_output
from app.services.ai_analyst.verification import verify_ai_output


def _sample_pack(**kwargs) -> EvidencePack:
    defaults = dict(
        org_id="org-1",
        org_name="Test Org",
        period="2026-06",
        generated_at=datetime.now(timezone.utc),
        coverage=EvidencePackCoverage(
            sectors={"financials": True},
            domains={"ar_aging": True},
            sectors_count=1,
        ),
        confidence=EvidencePackConfidence(
            legacy_score=15,
            normalized_score=0.25,
            components=EvidencePackConfidenceComponents(
                coverage_completeness=0.25,
                mapping_quality=0.9,
                cross_domain_joinability=0.1,
                temporal_depth=0.33,
            ),
        ),
        health=EvidencePackHealth(score=88, status="Stable", components=EvidencePackHealthComponents()),
        metrics={"ar": {"total_receivables": 50000.0, "over_90_percent": 5.0}},
        top_entities=EvidencePackTopEntities(),
        findings=[],
        data_gaps=[
            EvidencePackDataGap(upload="GL Detail", confidence_lift=0.1, reason_code="missing_gl"),
        ],
        memory=EvidencePackMemory(enabled=False, recurring_findings=[]),
    )
    defaults.update(kwargs)
    return EvidencePack(**defaults)


def test_deterministic_fallback_passes_verification():
    pack = _sample_pack(
        findings=[],
        metrics={"ar": {"total_receivables": 100000.0, "over_90_percent": 2.0}},
    )
    output = build_deterministic_analyst_output(pack)
    result = verify_ai_output(pack, output)
    assert result.passed is True
    assert output.source == "deterministic_fallback"


def test_verify_rejects_untraceable_numbers():
    pack = _sample_pack(metrics={"ar": {"total_receivables": 1000.0}})
    output = AnalystOutput(
        executive_summary=["Unexpected balance of $999999 is critical."],
        recommended_uploads=[
            RecommendedUpload(
                upload="GL Detail",
                rationale="Need GL",
                reason_code="missing_gl",
            )
        ],
    )
    result = verify_ai_output(pack, output)
    assert result.passed is False
    assert any("999999" in f for f in result.failures)


def test_verify_rejects_unknown_upload():
    pack = _sample_pack()
    output = AnalystOutput(
        recommended_uploads=[
            RecommendedUpload(
                upload="Alien ERP Export",
                rationale="Unknown",
                reason_code="unknown",
            )
        ],
    )
    result = verify_ai_output(pack, output)
    assert result.passed is False


def test_fallback_recommended_uploads_trace_to_gaps():
    pack = _sample_pack(
        data_gaps=[
            EvidencePackDataGap(upload="Open Sales Orders", confidence_lift=0.15, reason_code="missing_so"),
        ]
    )
    output = build_deterministic_analyst_output(pack)
    uploads = {u.upload for u in output.recommended_uploads}
    assert "Open Sales Orders" in uploads
