from __future__ import annotations

import secrets
import uuid

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import DEV_API_KEY, settings
from app.database import get_db
from app.models import Organization


def _configured_api_key() -> str:
    key = (settings.api_key or "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="API key not configured")
    if settings.is_production and key == DEV_API_KEY:
        raise HTTPException(status_code=503, detail="API key not configured")
    return key


def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")):
    expected = _configured_api_key()
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


def verify_admin_key(x_admin_key: str | None = Header(None, alias="X-Admin-Key")):
    expected = (settings.admin_api_key or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Admin API not configured")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
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
