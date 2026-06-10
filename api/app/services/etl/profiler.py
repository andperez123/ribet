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


_ID_HEADER_TOKENS = frozenset({"id", "no", "number", "num", "code", "account", "sku", "invoice", "po"})


@dataclass
class DataProfile:
    file_name: str
    row_count: int
    column_count: int
    headers: list[str]
    sample_rows: list[dict]
    column_profiles: list[ColumnProfile]
    detected_date_columns: list[str]
    detected_money_columns: list[str]
    detected_id_columns: list[str]
    null_rates: dict[str, float]
    duplicate_rates: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "headers": self.headers,
            "sample_rows": self.sample_rows,
            "column_profiles": [p.to_dict() for p in self.column_profiles],
            "detected_date_columns": self.detected_date_columns,
            "detected_money_columns": self.detected_money_columns,
            "detected_id_columns": self.detected_id_columns,
            "null_rates": {k: round(v, 3) for k, v in self.null_rates.items()},
            "duplicate_rates": {k: round(v, 3) for k, v in self.duplicate_rates.items()},
        }


def _looks_id_column(name: str, profile: ColumnProfile) -> bool:
    lower = name.lower()
    tokens = set(re.findall(r"[a-z0-9]+", lower))
    if tokens & _ID_HEADER_TOKENS:
        return profile.uniqueness_ratio >= 0.5 or profile.looks_numeric
    return profile.uniqueness_ratio >= 0.85 and not profile.looks_date


def profile_upload(df: pd.DataFrame, file_name: str, max_samples: int = 5) -> DataProfile:
    """Build file-level DataProfile from a dataframe."""
    profiles = profile_dataframe(df, max_samples=max_samples)
    null_rates = {p.name: p.null_rate for p in profiles}
    duplicate_rates: dict[str, float] = {}
    for p in profiles:
        duplicate_rates[p.name] = max(0.0, 1.0 - p.uniqueness_ratio)

    detected_date = [p.name for p in profiles if p.looks_date]
    detected_money = [
        p.name for p in profiles if p.looks_currency or (p.looks_numeric and not p.looks_date)
    ]
    detected_id = [p.name for p in profiles if _looks_id_column(p.name, p)]

    sample_rows = (
        df.head(max_samples).fillna("").astype(str).to_dict(orient="records")
        if len(df) > 0
        else []
    )

    return DataProfile(
        file_name=file_name,
        row_count=len(df),
        column_count=len(df.columns),
        headers=[str(c) for c in df.columns],
        sample_rows=sample_rows,
        column_profiles=profiles,
        detected_date_columns=detected_date,
        detected_money_columns=detected_money,
        detected_id_columns=detected_id,
        null_rates=null_rates,
        duplicate_rates=duplicate_rates,
    )


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
