import io
import os
from pathlib import Path
from uuid import UUID

from app.config import settings

LOCAL_STORAGE = Path(os.environ.get("LOCAL_STORAGE_PATH", "/tmp/ribet-uploads"))


def _use_local() -> bool:
    return os.environ.get("STORAGE_BACKEND", "").lower() == "local"


def get_s3_client():
    import boto3
    from botocore.client import Config

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def upload_file(org_id: UUID, job_id: UUID, filename: str, content: bytes) -> str:
    key = f"{org_id}/{job_id}/{filename}"
    if _use_local():
        path = LOCAL_STORAGE / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key
    client = get_s3_client()
    client.put_object(Bucket=settings.s3_bucket, Key=key, Body=content)
    return key


def download_file(storage_key: str) -> bytes:
    if _use_local():
        return (LOCAL_STORAGE / storage_key).read_bytes()
    client = get_s3_client()
    obj = client.get_object(Bucket=settings.s3_bucket, Key=storage_key)
    return obj["Body"].read()


def read_file_to_dataframe(storage_key: str, filename: str):
    import pandas as pd

    content = download_file(storage_key)
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    if filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content))
    raise ValueError(f"Unsupported file type: {filename}")
