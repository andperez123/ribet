import os
from pathlib import Path, PurePosixPath
from uuid import UUID

from app.config import settings

LOCAL_STORAGE = Path(os.environ.get("LOCAL_STORAGE_PATH", "/tmp/ribet-uploads"))


def _use_local() -> bool:
    backend = (os.environ.get("STORAGE_BACKEND") or settings.storage_backend or "").lower()
    return backend == "local"


def _safe_filename(filename: str) -> str:
    """Basename only — reject path traversal in upload names."""
    name = PurePosixPath(filename.replace("\\", "/")).name.strip().replace("\x00", "")
    if not name or name in {".", ".."} or ".." in name:
        return "upload"
    return name[:255]


def _local_path_for_key(key: str) -> Path:
    root = LOCAL_STORAGE.resolve()
    path = (LOCAL_STORAGE / key).resolve()
    if path != root and root not in path.parents:
        raise ValueError("Invalid storage path")
    return path


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
    safe_name = _safe_filename(filename)
    key = f"{org_id}/{job_id}/{safe_name}"
    if _use_local():
        path = _local_path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key
    client = get_s3_client()
    client.put_object(Bucket=settings.s3_bucket, Key=key, Body=content)
    return key


def download_file(storage_key: str) -> bytes:
    if _use_local():
        return _local_path_for_key(storage_key).read_bytes()
    client = get_s3_client()
    obj = client.get_object(Bucket=settings.s3_bucket, Key=storage_key)
    return obj["Body"].read()


def read_file_to_dataframe(storage_key: str, filename: str):
    """Legacy entry point — returns dataframe only."""
    return read_upload_to_dataframe(storage_key, filename).dataframe


def read_upload_to_dataframe(storage_key: str, filename: str):
    from app.services.etl.file_intake import intake_file

    content = download_file(storage_key)
    return intake_file(content, filename)
