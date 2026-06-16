"""Report insights: digest, domain insights, legacy hydration, invariant."""

from app.models import OperationalReport, Organization
from app.services.digest import (
    DataDigest,
    TopEntry,
    build_domain_insights,
    build_executive_summary,
)
from app.services.report_insights import (
    hydrate_report_insights,
    serialize_insights_for_api,
    validate_insights_invariant,
)


def test_build_domain_insights_from_digest():
    digest = DataDigest(
        ar_total=100_000,
        ar_over_90=8_000,
        ar_over_90_pct=8.0,
        ar_invoice_count=42,
        top_customers=[TopEntry(label="Acme Corp", amount=30_000, pct=30.0)],
    )
    insights = build_domain_insights(digest, [])
    assert len(insights) >= 2
    assert any(i.domain == "ar" for i in insights)
    validate_insights_invariant(digest.to_dict(), [i.to_dict() for i in insights])


def test_executive_summary_empty_digest():
    digest = DataDigest()
    lines = build_executive_summary(digest, [])
    assert len(lines) == 1
    assert "Upload AR/AP/GL/inventory" in lines[0]


def test_executive_summary_with_ar():
    digest = DataDigest(ar_total=50_000, ar_invoice_count=10, ar_over_90_pct=5.0)
    lines = build_executive_summary(digest, [])
    assert any("receivables" in line.lower() for line in lines)


def test_insight_invariant_fails_when_empty_insights():
    digest = DataDigest(ar_total=10_000, ar_invoice_count=1)
    try:
        validate_insights_invariant(digest.to_dict(), [])
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "domain_insights is empty" in str(e)


def test_serialize_fallback_narration_metadata():
    from app.services.report_insights import ReportInsightsBundle

    bundle = ReportInsightsBundle(
        data_digest={},
        domain_insights=[],
        data_coverage={"ar": False, "ap": False, "gl": False, "inventory": False},
        analysis_metadata={
            "narration": "fallback",
            "finding_count": 3,
            "data_domains_present": ["ar", "ap"],
            "used_fallback": True,
            "verification_status": "fallback",
        },
    )
    serialized = serialize_insights_for_api(bundle)
    assert serialized["analysis_metadata"]["narration"] == "fallback"


def test_hydrate_legacy_report_computes_on_read(client):
    from app.database import SessionLocal
    from app.seed import DEMO_ORG_ID

    db = SessionLocal()
    org = db.get(Organization, DEMO_ORG_ID)
    if not org:
        db.add(Organization(id=DEMO_ORG_ID, name="Test", erp_family="jobboss"))
        db.commit()

    report = OperationalReport(
        org_id=DEMO_ORG_ID,
        executive_summary=["Legacy summary"],
        health_score=100,
        health_status="Stable",
    )
    db.add(report)
    db.commit()

    bundle = hydrate_report_insights(db, report)
    assert bundle.hydrated is True
    assert bundle.data_coverage["ar"] is False
    assert bundle.data_coverage["ap"] is False
    serialized = serialize_insights_for_api(bundle)
    assert "data_digest" in serialized
    assert serialized["domain_insights"] == []
    db.close()

