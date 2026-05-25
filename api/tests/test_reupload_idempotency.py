import uuid
from io import StringIO

import pandas as pd

from app.models import Invoice, Organization
from app.services.etl.generic.parser import parse_ar_aging
from tests.conftest import TestSession, engine
from app.database import Base


def test_reupload_replaces_period_rows():
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    org = Organization(name="Reupload Test", erp_family="generic")
    session.add(org)
    session.commit()
    session.refresh(org)
    job_id = uuid.uuid4()

    df1 = pd.read_csv(
        StringIO(
            "customer_id,invoice_id,amount,days_overdue\n"
            "C1,INV1,1000,10\n"
            "C2,INV2,2000,95\n"
        )
    )
    parse_ar_aging(session, org.id, job_id, df1)
    session.commit()
    assert session.query(Invoice).filter(Invoice.org_id == org.id).count() == 2

    df2 = pd.read_csv(
        StringIO("customer_id,invoice_id,amount,days_overdue\nC1,INV1,5000,5\n")
    )
    parse_ar_aging(session, org.id, job_id, df2)
    session.commit()
    rows = session.query(Invoice).filter(Invoice.org_id == org.id).all()
    assert len(rows) == 1
    assert rows[0].amount == 5000
    session.close()
