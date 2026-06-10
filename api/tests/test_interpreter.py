"""Tests for dynamic ERP export interpreter — TBAL, readiness, schema memory."""

from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import GlTransaction, Organization
from app.services.etl.classifier import classify_dataset
from app.services.etl.interpretation import interpret_upload
from app.services.mapping_memory import check_schema_memory, save_org_mapping_memory
from app.services.etl.field_mapper import MappingPlan, propose_mapping
from app.services.etl.profiler import profile_upload
from app.services.transforms.adapters.generic import dataframe_to_canonical
from app.services.transforms.persist import persist_canonical

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    org = Organization(id=uuid4(), name="Interpreter Test Org", erp_family="generic")
    session.add(org)
    session.commit()
    yield session, org
    session.close()


def test_tbal_classified_with_high_confidence():
    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    classification = classify_dataset(
        "V_BI_GL_TBAL.csv",
        list(df.columns),
        profile_upload(df, "V_BI_GL_TBAL.csv").column_profiles,
    )
    assert classification.likely_type == "gl_trial_balance"
    assert classification.confidence >= 0.75
    assert "gl_accounts" in classification.detected_entities


def test_tbal_low_readiness_until_amount_strategy():
    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    result = interpret_upload(df, "V_BI_GL_TBAL.csv")
    assert result.classification.likely_type == "gl_trial_balance"
    assert result.readiness is not None
    assert result.readiness.ready is False
    assert result.readiness.score <= 0.5
    assert any(q.id == "gl_amount_semantics" for q in result.questions)


def test_tbal_row_meaning_inferred():
    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    result = interpret_upload(df, "V_BI_GL_TBAL.csv")
    assert result.row_meaning.inferred == "one_gl_account_balance"
    assert result.row_meaning.confidence >= 0.85


def test_tbal_net_activity_strategy(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    profiles = profile_upload(df, "gl_trial_balance.csv").column_profiles
    plan = propose_mapping(profiles, "gl_trial_balance", list(df.columns))
    plan.amount_strategy = "net_activity"

    dataset = dataframe_to_canonical("gl_trial_balance", df, plan=plan)
    assert len(dataset.gl_trial_balance) == 3
    assert len(dataset.gl) == 3

    row = dataset.gl_trial_balance[1]
    assert float(row.net_activity) == pytest.approx(float(row.ending_balance - row.beginning_balance))

    job_id = uuid4()
    rows = persist_canonical(session, org.id, job_id, "2026-06", dataset)
    session.commit()
    assert rows == 3
    gl_rows = session.query(GlTransaction).filter(GlTransaction.org_id == org.id).all()
    assert len(gl_rows) == 3


def test_tbal_with_mapping_answers_ready(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    answers = {"gl_amount_semantics": "net_activity", "row_meaning": "one_gl_account_balance"}
    result = interpret_upload(df, "gl_trial_balance.csv", org=org, mapping_answers=answers, user_confirmed=True)
    plan = result.mapping_plan
    plan.amount_strategy = "net_activity"
    dataset = dataframe_to_canonical("gl_trial_balance", df, plan=plan)
    assert dataset.coverage_score > 0


def test_schema_memory_auto_apply_same_org(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    columns = list(df.columns)
    plan = MappingPlan(report_type="gl_trial_balance", field_mapping={}, column_map={"ACCOUNT": "account_id"})
    save_org_mapping_memory(
        org,
        plan,
        columns,
        mapping_answers={"gl_amount_semantics": "net_activity"},
        row_meaning="one_gl_account_balance",
    )
    session.commit()

    match = check_schema_memory(org, "gl_trial_balance", columns)
    assert match.match == "auto_apply"


def test_schema_memory_none_for_other_org(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    columns = list(df.columns)
    plan = MappingPlan(report_type="gl_trial_balance", field_mapping={}, column_map={"ACCOUNT": "account_id"})
    save_org_mapping_memory(org, plan, columns, mapping_answers={"gl_amount_semantics": "net_activity"})
    session.commit()

    other_org = Organization(id=uuid4(), name="Other Org", erp_family="generic")
    session.add(other_org)
    session.commit()
    other_match = check_schema_memory(other_org, "gl_trial_balance", columns)
    assert other_match.match == "none"


def test_tbal_metadata_is_json_serializable():
    import json

    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    result = interpret_upload(df, "V_BI_GL_TBAL.csv")
    json.dumps(result.to_metadata())


def test_acct_desc_maps_to_account_name():
    df = pd.read_csv(FIXTURES / "gl_trial_balance.csv")
    profiles = profile_upload(df, "gl_trial_balance.csv").column_profiles
    plan = propose_mapping(profiles, "gl_trial_balance", list(df.columns))
    assert plan.field_mapping.get("account_name") is not None
    assert plan.field_mapping["account_name"].source == "ACCT_DESC"
