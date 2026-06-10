"""Evidence-based dataset classification — not filename-first."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.services.etl.profiler import ColumnProfile, DataProfile

LikelyType = Literal[
    "ar_aging",
    "ap_aging",
    "inventory",
    "gl_detail",
    "gl_trial_balance",
    "purchase_orders",
    "sales_orders",
    "jobs",
    "timecards",
    "unknown_operational_export",
    "unknown",
]

_CLASS_LABELS: dict[str, str] = {
    "ar_aging": "AR Aging",
    "ap_aging": "AP Aging",
    "inventory": "Inventory",
    "gl_detail": "GL Detail",
    "gl_trial_balance": "GL Trial Balance",
    "purchase_orders": "Purchase Orders",
    "sales_orders": "Sales Orders",
    "jobs": "Jobs",
    "timecards": "Timecards",
    "unknown_operational_export": "Unknown Operational Export",
    "unknown": "Unknown",
}


@dataclass
class DatasetClassification:
    likely_type: LikelyType
    confidence: float
    evidence: list[str] = field(default_factory=list)
    alternative_types: list[tuple[str, float]] = field(default_factory=list)
    detected_entities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "likely_type": self.likely_type,
            "label": _CLASS_LABELS.get(self.likely_type, self.likely_type),
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "alternative_types": [
                {"type": t, "label": _CLASS_LABELS.get(t, t), "confidence": round(s, 3)}
                for t, s in self.alternative_types
            ],
            "detected_entities": self.detected_entities,
        }


def _col_text(columns: list[str]) -> str:
    return " ".join(str(c).lower() for c in columns)


def _has_token(text: str, *tokens: str) -> bool:
    return any(t in text for t in tokens)


def _detect_entities(columns: list[str], cols_lower: str) -> list[str]:
    entities: list[str] = []
    if _has_token(cols_lower, "customer", "client", "cust"):
        entities.append("customers")
    if _has_token(cols_lower, "vendor", "supplier"):
        entities.append("vendors")
    if _has_token(cols_lower, "invoice", "inv no", "inv #"):
        entities.append("invoices")
    if _has_token(cols_lower, "purchase order", "po number", "po #", "po no"):
        entities.append("purchase_orders")
    if _has_token(cols_lower, "sales order", "so number", "so #"):
        entities.append("sales_orders")
    if _has_token(cols_lower, "account", "acct", "gl"):
        entities.append("gl_accounts")
    if _has_token(cols_lower, "sku", "part", "item", "inventory"):
        entities.append("parts")
    if _has_token(cols_lower, "job", "work order", "wo "):
        entities.append("jobs")
    if _has_token(cols_lower, "timecard", "hours", "punch"):
        entities.append("timecards")
    return entities


def _is_trial_balance_layout(columns: list[str], profiles: list[ColumnProfile]) -> tuple[float, list[str]]:
    cols_lower = _col_text(columns)
    evidence: list[str] = []
    score = 0.0

    has_account = _has_token(cols_lower, "account", "acct")
    has_debit = _has_token(cols_lower, "debit")
    has_credit = _has_token(cols_lower, "credit")
    has_beg = bool(re.search(r"beg.*bal|beginning.*bal", cols_lower))
    has_end = bool(re.search(r"end.*bal|ending.*bal", cols_lower))
    has_txn_date = _has_token(cols_lower, "posting date", "transaction date", "trans date", "posted")

    if has_account:
        score += 0.2
        evidence.append("account column detected")
    if has_debit and has_credit:
        score += 0.25
        evidence.append("debit/credit columns detected")
    if has_beg and has_end:
        score += 0.25
        evidence.append("begin/end balance columns detected")
    if not has_txn_date:
        score += 0.1
        evidence.append("no transaction date column")
    if _has_token(cols_lower, "tbal", "trial balance", "trial bal"):
        score += 0.15
        evidence.append("trial balance signal in headers")

    money_cols = sum(1 for p in profiles if p.looks_numeric or p.looks_currency)
    if money_cols >= 3:
        score += 0.05

    return min(score, 1.0), evidence


def _score_type(
    report_type: str,
    columns: list[str],
    filename: str,
    profiles: list[ColumnProfile],
    sector_hint: str | None,
) -> tuple[float, list[str]]:
    cols_lower = _col_text(columns)
    name_lower = filename.lower()
    evidence: list[str] = []
    score = 0.0

    signatures: dict[str, list[str]] = {
        "ar_aging": ["customer", "aging", "overdue", "days", "balance", "invoice"],
        "ap_aging": ["vendor", "aging", "balance", "payable", "owed"],
        "gl_detail": ["account", "amount", "journal", "posting", "transaction date"],
        "gl_trial_balance": [],
        "inventory": ["sku", "item", "quantity", "qty", "on hand", "inventory"],
        "purchase_orders": ["purchase order", "po number", "po #", "promise date", "receipt"],
        "sales_orders": ["sales order", "so number", "ship date", "order qty", "backorder"],
        "jobs": ["job", "work order", "operation", "wo "],
        "timecards": ["timecard", "hours", "punch", "employee"],
    }

    if report_type == "gl_trial_balance":
        return _is_trial_balance_layout(columns, profiles)

    keywords = signatures.get(report_type, [])
    hits = sum(1 for kw in keywords if kw in cols_lower or kw in name_lower)
    if hits:
        score = min(0.35 + hits * 0.12, 0.95)
        evidence.append(f"{hits} header/filename signal(s) for {report_type}")

    filename_boosts = {
        "ar_aging": [("ar", "aging")],
        "ap_aging": [("ap", "aging")],
        "purchase_orders": [("purchase", "order")],
        "sales_orders": [("sales", "order")],
        "inventory": [("inventory",), ("inv",)],
        "gl_detail": [("journal",), ("gl detail",)],
        "gl_trial_balance": [("tbal",), ("trial balance",), ("trial bal",)],
    }
    for pair in filename_boosts.get(report_type, []):
        if all(p in name_lower for p in pair):
            score = min(score + 0.15, 0.95)
            evidence.append(f"filename suggests {report_type}")
            break

    if sector_hint:
        sector_map = {
            "financials": ["ar_aging", "ap_aging", "gl_detail", "gl_trial_balance"],
            "manufacturing": ["inventory", "jobs"],
            "orders": ["purchase_orders", "ap_aging"],
            "sales": ["sales_orders", "ar_aging"],
        }
        if report_type in sector_map.get(sector_hint, []):
            score = min(score + 0.08, 0.95)
            evidence.append(f"sector hint supports {report_type}")

    return score, evidence


def classify_dataset(
    filename: str,
    columns: list[str],
    profiles: list[ColumnProfile] | None = None,
    data_profile: DataProfile | None = None,
    sector_hint: str | None = None,
) -> DatasetClassification:
    if profiles is None and data_profile is not None:
        profiles = data_profile.column_profiles
    profiles = profiles or []

    candidates = [
        "gl_trial_balance",
        "ar_aging",
        "ap_aging",
        "gl_detail",
        "inventory",
        "purchase_orders",
        "sales_orders",
        "jobs",
        "timecards",
    ]

    scored: list[tuple[str, float, list[str]]] = []
    for report_type in candidates:
        s, ev = _score_type(report_type, columns, filename, profiles, sector_hint)
        if s > 0:
            scored.append((report_type, s, ev))

    scored.sort(key=lambda x: x[1], reverse=True)

    entities = _detect_entities(columns, _col_text(columns))

    if not scored or scored[0][1] < 0.35:
        return DatasetClassification(
            likely_type="unknown_operational_export",
            confidence=0.42 if scored else 0.25,
            evidence=["no strong match to known export types"] + (scored[0][2] if scored else []),
            alternative_types=[(t, s) for t, s, _ in scored[:3]],
            detected_entities=entities,
        )

    best_type, best_score, best_evidence = scored[0]
    alternatives = [(t, s) for t, s, _ in scored[1:4] if s >= 0.25]

    return DatasetClassification(
        likely_type=best_type,  # type: ignore[arg-type]
        confidence=best_score,
        evidence=best_evidence,
        alternative_types=alternatives,
        detected_entities=entities,
    )
