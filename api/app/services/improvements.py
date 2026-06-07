"""Improvement notes — compare current upload to prior snapshot in a series."""

from __future__ import annotations

from dataclasses import dataclass

from app.models import SeriesSnapshot


@dataclass
class ImprovementNote:
    metric: str
    direction: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "direction": self.direction,
            "message": self.message,
            "severity": self.severity,
        }


def build_improvement_notes(
    current_kpi: dict,
    prior: SeriesSnapshot | None,
) -> list[dict]:
    if not prior or not prior.kpi_summary:
        return []

    prev = prior.kpi_summary
    notes: list[ImprovementNote] = []

    cur_ar90 = current_kpi.get("ar_over_90_pct")
    prev_ar90 = prev.get("ar_over_90_pct")
    if cur_ar90 is not None and prev_ar90 is not None:
        delta = cur_ar90 - prev_ar90
        if abs(delta) >= 1:
            if delta < 0:
                notes.append(
                    ImprovementNote(
                        metric="ar_over_90_pct",
                        direction="improved",
                        message=(
                            f"AR over 90 days improved: {prev_ar90:.1f}% → {cur_ar90:.1f}% "
                            f"({delta:.1f}pp)"
                        ),
                        severity="info",
                    )
                )
            else:
                notes.append(
                    ImprovementNote(
                        metric="ar_over_90_pct",
                        direction="worsened",
                        message=(
                            f"AR over 90 days increased: {prev_ar90:.1f}% → {cur_ar90:.1f}% "
                            f"(+{delta:.1f}pp)"
                        ),
                        severity="warning",
                    )
                )

    cur_health = current_kpi.get("health_score")
    prev_health = prev.get("health_score")
    if cur_health is not None and prev_health is not None:
        delta = cur_health - prev_health
        if abs(delta) >= 3:
            direction = "improved" if delta > 0 else "worsened"
            notes.append(
                ImprovementNote(
                    metric="health_score",
                    direction=direction,
                    message=f"Health score: {prev_health} → {cur_health} ({'+' if delta > 0 else ''}{delta})",
                    severity="info" if delta > 0 else "warning",
                )
            )

    cur_ar = current_kpi.get("ar_total")
    prev_ar = prev.get("ar_total")
    if cur_ar and prev_ar and prev_ar > 0:
        pct_change = abs(cur_ar - prev_ar) / prev_ar * 100
        if pct_change >= 15:
            notes.append(
                ImprovementNote(
                    metric="ar_total",
                    direction="changed",
                    message=f"Total AR changed by {pct_change:.0f}% vs prior upload",
                    severity="info",
                )
            )

    return [n.to_dict() for n in notes]
