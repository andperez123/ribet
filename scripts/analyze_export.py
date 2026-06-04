#!/usr/bin/env python3
"""Phase 1 testing harness: analyze a set of ERP exports end-to-end.

Read-only. Ingests CSV/XLSX exports the same way the worker does
(detector -> alias normalization -> generic adapter -> persist), into an
in-memory SQLite DB, then runs BEFORE (legacy rules) vs AFTER (Phase 1 rules)
analysis plus the new digest and executive summary.

It also reports, per file:
  - detected report type
  - which columns mapped to canonical fields
  - which columns were UNMAPPED (input for the Phase 2 field-mapping layer)

Usage:
    python scripts/analyze_export.py [DIR_OR_FILES ...]

Defaults to the repo `fixtures/` directory when no paths are given.

Run from the repo root with the api deps available, e.g.:
    PYTHONPATH=api python scripts/analyze_export.py /path/to/erp_exports
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

# Configure a throwaway environment before importing app modules.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("RIBET_ENV", "test")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("RIBET_NARRATION", "off")

REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import pandas as pd  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base  # noqa: E402
from app.models import Organization  # noqa: E402
from app.services.etl.aliases import normalize_columns  # noqa: E402
from app.services.etl.detector import detect_report_type  # noqa: E402
from app.services.transforms.adapters.generic import dataframe_to_canonical  # noqa: E402
from app.services.transforms.persist import persist_canonical  # noqa: E402
from app.services.digest import build_data_digest, build_executive_summary  # noqa: E402
from app.services.rules import runner  # noqa: E402

LEGACY_RULES = [
    "_check_ar_aging_spike",
    "_check_duplicate_customers",
    "_check_ap_negative",
    "_check_vendor_concentration",
    "_check_inventory_adjustments",
    "_check_orphan_inventory",
    "_check_missing_gl_mappings",
    "_check_invalid_aging_buckets",
    "_check_duplicate_vendors",
]


def _read_df(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {path.name}")


def _collect_files(args: list[str]) -> list[Path]:
    paths: list[Path] = []
    targets = args or [str(REPO_ROOT / "fixtures")]
    for t in targets:
        p = Path(t)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.csv")))
            paths.extend(sorted(p.glob("*.xls*")))
        elif p.exists():
            paths.append(p)
        else:
            print(f"  ! skipping missing path: {t}")
    return paths


def _run_rule_subset(db, org_id, names: list[str]):
    findings = []
    for n in names:
        fn = getattr(runner, n)
        findings.extend(fn(db, org_id))
    return findings


def _fmt_findings(findings) -> list[str]:
    lines = []
    for f in sorted(findings, key=lambda x: x.severity):
        lines.append(f"    [{f.severity.upper():8}] {f.title} — {f.detail}")
    return lines


def main() -> int:
    files = _collect_files(sys.argv[1:])
    if not files:
        print("No input files found.")
        return 1

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    org = Organization(id=uuid4(), name="Test Export Org", erp_family="jobboss")
    db.add(org)
    db.flush()

    print("=" * 78)
    print("INGESTION + COLUMN MAPPING")
    print("=" * 78)
    for path in files:
        try:
            df = _read_df(path)
        except Exception as e:  # noqa: BLE001
            print(f"\n{path.name}: FAILED to read — {e}")
            continue
        cols = list(df.columns)
        report_type = detect_report_type(path.name, cols)
        col_map = normalize_columns(cols)
        mapped = {orig: canon for orig, canon in col_map.items()}
        unmapped = [c for c in cols if c not in mapped]

        dataset = dataframe_to_canonical(report_type, df)
        job_id = uuid4()
        rows = persist_canonical(db, org.id, job_id, "period-test", dataset)

        print(f"\n{path.name}")
        print(f"  detected_type : {report_type}")
        print(f"  rows_ingested : {rows} (of {len(df)} source rows)")
        print(f"  mapped_cols   : {mapped or '(none)'}")
        print(f"  UNMAPPED_cols : {unmapped or '(none)'}   <-- Phase 2 mapping candidates")
    db.flush()

    print("\n" + "=" * 78)
    print("ANALYSIS: BEFORE (legacy rules) vs AFTER (Phase 1 rules)")
    print("=" * 78)
    before = _run_rule_subset(db, org.id, LEGACY_RULES)
    after = runner.run_rules(db, org.id)

    before_types = {f.finding_type for f in before}
    new_findings = [f for f in after if f.finding_type not in before_types]

    print(f"\nBEFORE: {len(before)} finding(s)")
    for line in _fmt_findings(before):
        print(line)

    print(f"\nAFTER:  {len(after)} finding(s)")
    for line in _fmt_findings(after):
        print(line)

    print(f"\nNEW in AFTER (caught by Phase 1, missed before): {len(new_findings)}")
    for line in _fmt_findings(new_findings):
        print(line)

    print("\n" + "=" * 78)
    print("DATA DIGEST")
    print("=" * 78)
    digest = build_data_digest(db, org.id)
    d = digest.to_dict()
    for k, v in d.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 78)
    print("EXECUTIVE SUMMARY (deterministic, no LLM)")
    print("=" * 78)
    for line in build_executive_summary(digest, after):
        print(f"  - {line}")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
