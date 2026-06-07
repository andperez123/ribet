from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def period_from_dataframe(
    df: pd.DataFrame,
    column_map: dict[str, str] | None = None,
    fallback: str | None = None,
) -> str:
    canonical_date_fields = ("posted_at", "due_date", "posting_date", "date")
    cols_to_check: list[str] = []

    if column_map:
        for orig, canonical in column_map.items():
            if canonical in canonical_date_fields and orig in df.columns:
                cols_to_check.append(orig)
    for col in canonical_date_fields:
        if col in df.columns and col not in cols_to_check:
            cols_to_check.append(col)

    for col in cols_to_check:
        if col in df.columns:
            dates = pd.to_datetime(df[col], errors="coerce").dropna()
            if len(dates):
                return dates.max().strftime("%Y-%m")
    return fallback or datetime.now(timezone.utc).strftime("%Y-%m")
