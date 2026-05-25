"""Transform upload: detector → adapter → canonical → persist → snapshot."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Organization
from app.services.etl.detector import detect_report_type
from app.services.storage import read_file_to_dataframe
from app.services.transforms.adapters import generic as generic_adapter
from app.services.transforms.adapters import jobboss as jobboss_adapter
from app.services.transforms.normalization.periods import period_from_dataframe
from app.services.transforms.persist import persist_canonical
from app.services.transforms.snapshot import build_operational_snapshot


@dataclass
class TransformResult:
    report_type: str
    period: str
    row_count: int


def transform_upload(
    db: Session,
    org: Organization,
    job_id: UUID,
    filename: str,
    storage_key: str,
) -> TransformResult:
    df = read_file_to_dataframe(storage_key, filename)
    report_type = detect_report_type(filename, list(df.columns))
    period = period_from_dataframe(df)

    adapter_module = (
        jobboss_adapter if org.erp_family == "jobboss" else generic_adapter
    )
    dataset = adapter_module.dataframe_to_canonical(report_type, df)
    row_count = persist_canonical(db, org.id, job_id, period, dataset)

    return TransformResult(report_type=report_type, period=period, row_count=row_count)
