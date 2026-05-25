from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def period_from_dataframe(df: pd.DataFrame, fallback: str | None = None) -> str:
    for col in ("posting_date", "due_date", "posted_at", "date"):
        if col in df.columns:
            dates = pd.to_datetime(df[col], errors="coerce").dropna()
            if len(dates):
                return dates.max().strftime("%Y-%m")
    return fallback or datetime.now(timezone.utc).strftime("%Y-%m")
