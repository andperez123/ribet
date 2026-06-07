"""Column profiling for heuristic mapping."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

_CURRENCY_RE = re.compile(r"[$€£]")
_DATE_RE = re.compile(r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}")


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    null_rate: float
    uniqueness_ratio: float
    looks_currency: bool
    looks_date: bool
    looks_numeric: bool
    sample_values: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "null_rate": round(self.null_rate, 3),
            "uniqueness_ratio": round(self.uniqueness_ratio, 3),
            "looks_currency": self.looks_currency,
            "looks_date": self.looks_date,
            "looks_numeric": self.looks_numeric,
            "sample_values": self.sample_values,
        }


def _looks_currency(series: pd.Series) -> bool:
    sample = series.dropna().astype(str).head(20)
    if sample.empty:
        return False
    hits = sum(1 for v in sample if _CURRENCY_RE.search(v) or "," in v)
    return hits / len(sample) >= 0.3


def _looks_date(series: pd.Series) -> bool:
    sample = series.dropna().astype(str).head(20)
    if sample.empty:
        return False
    hits = sum(1 for v in sample if _DATE_RE.search(v))
    if hits / len(sample) >= 0.5:
        return True
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.notna().mean() >= 0.5


def _looks_numeric(series: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(series):
        return True
    sample = series.dropna().astype(str).head(30)
    if sample.empty:
        return False
    ok = 0
    for v in sample:
        try:
            float(str(v).replace(",", "").replace("$", "").strip())
            ok += 1
        except ValueError:
            pass
    return ok / len(sample) >= 0.7


def profile_dataframe(df: pd.DataFrame, max_samples: int = 5) -> list[ColumnProfile]:
    profiles: list[ColumnProfile] = []
    n = max(len(df), 1)
    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        uniq = len(non_null.unique()) / max(len(non_null), 1)
        samples = [str(v)[:80] for v in non_null.head(max_samples).tolist()]
        profiles.append(
            ColumnProfile(
                name=str(col),
                dtype=str(series.dtype),
                null_rate=float(series.isna().mean()),
                uniqueness_ratio=float(uniq),
                looks_currency=_looks_currency(series),
                looks_date=_looks_date(series),
                looks_numeric=_looks_numeric(series),
                sample_values=samples,
            )
        )
    return profiles
