from __future__ import annotations

"""Analysis confidence score from graph coverage."""

from dataclasses import dataclass, field

from app.services.graph.coverage import COVERAGE_SPECS, GraphCoverage

CONFIDENCE_WEIGHTS: dict[str, int] = {
    "ar_aging": 15,
    "ap_aging": 15,
    "gl_detail": 10,
    "inventory": 15,
    "invoice_detail": 10,
    "sales_orders": 15,
    "purchase_orders": 10,
    "work_orders": 10,
}


@dataclass
class ConfidenceBreakdownItem:
    key: str
    label: str
    weight: int
    covered: bool


@dataclass
class UploadLift:
    key: str
    label: str
    confidence_if_uploaded: int


@dataclass
class ConfidenceResult:
    score: int
    breakdown: list[ConfidenceBreakdownItem] = field(default_factory=list)
    missing: list[ConfidenceBreakdownItem] = field(default_factory=list)
    upload_lifts: list[UploadLift] = field(default_factory=list)

    @property
    def next_upload(self) -> UploadLift | None:
        if not self.upload_lifts:
            return None
        return max(self.upload_lifts, key=lambda u: u.confidence_if_uploaded)


def compute_analysis_confidence(coverage: GraphCoverage) -> ConfidenceResult:
    breakdown: list[ConfidenceBreakdownItem] = []
    score = 0

    for spec in COVERAGE_SPECS:
        key = spec["key"]
        weight = CONFIDENCE_WEIGHTS.get(key, 0)
        covered = coverage.has(key)
        if covered:
            score += weight
        breakdown.append(
            ConfidenceBreakdownItem(
                key=key,
                label=spec["label"],
                weight=weight,
                covered=covered,
            )
        )

    missing = [b for b in breakdown if not b.covered]
    upload_lifts: list[UploadLift] = []

    for item in missing:
        if not _is_uploadable(item.key):
            continue
        lift_score = min(100, score + item.weight)
        upload_lifts.append(
            UploadLift(
                key=item.key,
                label=item.label,
                confidence_if_uploaded=lift_score,
            )
        )

    upload_lifts.sort(key=lambda u: u.confidence_if_uploaded, reverse=True)

    return ConfidenceResult(
        score=min(100, score),
        breakdown=breakdown,
        missing=missing,
        upload_lifts=upload_lifts,
    )


def confidence_if_keys_added(coverage: GraphCoverage, keys: list[str]) -> int:
    score = 0
    for spec in COVERAGE_SPECS:
        key = spec["key"]
        weight = CONFIDENCE_WEIGHTS.get(key, 0)
        if coverage.has(key) or key in keys:
            score += weight
    return min(100, score)


def _is_uploadable(key: str) -> bool:
    for spec in COVERAGE_SPECS:
        if spec["key"] == key:
            return spec["uploadable"]
    return False
