import uuid

from app.database import SessionLocal
from app.models import Organization

# Fixed UUIDs for dev — use in web/.env.local as DEV_ORG_ID
DEMO_ORG_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_ORG_B_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def seed_demo_orgs():
    db = SessionLocal()
    try:
        for org_id, name in [
            (DEMO_ORG_ID, "Demo Manufacturing Co"),
            (DEMO_ORG_B_ID, "Second Demo Shop"),
        ]:
            if not db.get(Organization, org_id):
                db.add(
                    Organization(
                        id=org_id,
                        name=name,
                        erp_family="jobboss",
                    )
                )
        db.commit()
    finally:
        db.close()
