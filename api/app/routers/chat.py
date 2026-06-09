from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import Organization
from app.services.chat import answer_operational_question

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    report_id: UUID | None = None


@router.post("/query")
def chat_query(
    body: ChatQueryRequest,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    try:
        return answer_operational_question(
            db,
            org.id,
            body.question,
            report_id=body.report_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
