from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Organization


def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")):
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def verify_admin_key(x_admin_key: str | None = Header(None, alias="X-Admin-Key")):
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin API not configured")
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


def get_org_id(x_org_id: str | None = Header(None, alias="X-Org-Id")) -> uuid.UUID:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id header required")
    try:
        return uuid.UUID(x_org_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid org ID") from e


def get_organization(
    org_id: uuid.UUID = Depends(get_org_id),
    db: Session = Depends(get_db),
) -> Organization:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org
