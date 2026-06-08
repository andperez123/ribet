from __future__ import annotations

"""Validate AI narration output against digest and finding numbers."""

import re

from app.services.digest import DataDigest
from app.services.rules.runner import RuleFinding

_NUMBER_RE = re.compile(
    r"(?<!\w)(?:\$?\d{1,3}(?:,\d{3})+(?:\.\d+)?|\$?\d+(?:\.\d+)?%?)(?!\w)"
)


def _extract_numbers(text: str) -> set[str]:
    nums: set[str] = set()
    for match in _NUMBER_RE.findall(text or ""):
        normalized = match.replace("$", "").replace(",", "").rstrip("%")
        if normalized:
            nums.add(normalized)
    return nums


def _allowed_numbers(digest: DataDigest | None, findings: list[RuleFinding]) -> set[str]:
    allowed: set[str] = set()
    if digest is None:
        return allowed

    d = digest.to_dict()
    for key, val in d.items():
        if isinstance(val, (int, float)) and val != 0:
            allowed.add(str(int(val)) if float(val).is_integer() else f"{val:.1f}".rstrip("0").rstrip("."))
            if isinstance(val, float):
                allowed.add(f"{val:.1f}")
                allowed.add(f"{val:.2f}")
        if key in ("top_customers", "top_vendors") and isinstance(val, list):
            for entry in val:
                if isinstance(entry, dict):
                    for k in ("amount", "pct"):
                        n = entry.get(k)
                        if isinstance(n, (int, float)):
                            allowed.add(str(int(n)) if float(n).is_integer() else f"{n:.1f}".rstrip("0").rstrip("."))

    for f in findings:
        for num in _extract_numbers(f.detail):
            allowed.add(num)
        for num in _extract_numbers(f.title):
            allowed.add(num)

    return allowed


def validate_narration_numbers(
    text: str,
    digest: DataDigest | None,
    findings: list[RuleFinding],
) -> tuple[bool, list[str]]:
    """Return (valid, list of unsupported numbers)."""
    if not text.strip():
        return True, []

    claimed = _extract_numbers(text)
    if not claimed:
        return True, []

    allowed = _allowed_numbers(digest, findings)
    unsupported: list[str] = []
    for num in claimed:
        if num in allowed:
            continue
        if any(num.startswith(a) or a.startswith(num) for a in allowed if len(a) >= 2):
            continue
        unsupported.append(num)

    return len(unsupported) == 0, unsupported


def digest_passes_validation(digest: DataDigest | None) -> bool:
    if digest is None:
        return False
    from app.services.digest import digest_has_data

    if not digest_has_data(digest):
        return False
    if digest.ar_invoice_count > 0 and digest.ar_total <= 0:
        return False
    if digest.vendor_count > 0 and digest.ap_total <= 0 and digest.ar_invoice_count == 0:
        return False
    return True
