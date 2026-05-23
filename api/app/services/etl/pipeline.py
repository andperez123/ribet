from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Organization
from app.services.etl.detector import detect_report_type
from app.services.etl.generic.parser import PARSERS
from app.services.etl.jobboss import JOBBOSS_PARSERS
from app.services.storage import read_file_to_dataframe


def run_etl(
    db: Session,
    org: Organization,
    job_id: UUID,
    filename: str,
    storage_key: str,
) -> tuple[str, int]:
    df = read_file_to_dataframe(storage_key, filename)
    report_type = detect_report_type(filename, list(df.columns))

    parsers = JOBBOSS_PARSERS if org.erp_family == "jobboss" else PARSERS
    parser = parsers.get(report_type)
    if not parser:
        return report_type, 0

    row_count = parser(db, org.id, job_id, df)
    return report_type, row_count
