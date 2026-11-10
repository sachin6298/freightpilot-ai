"""Document storage adapters. PostgreSQL BYTEA storage is handled by the document route."""
from pathlib import Path
from app.config import settings


def _client():
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required for S3 document storage") from exc
    kwargs = {"region_name": settings.S3_REGION or None}
    if settings.AWS_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
    if settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def store_file(path: Path, storage_key: str) -> None:
    if settings.STORAGE_BACKEND == "postgresql":
        raise RuntimeError("PostgreSQL document bytes must be stored through StoredDocument.content")
    if settings.STORAGE_BACKEND == "local":
        return
    if settings.STORAGE_BACKEND != "s3":
        raise RuntimeError("Unsupported document storage backend")
    extra = {"ServerSideEncryption": "AES256"} if not settings.S3_ENDPOINT_URL or "r2.cloudflarestorage.com" not in settings.S3_ENDPOINT_URL else {}
    _client().upload_file(str(path), settings.S3_BUCKET, storage_key, ExtraArgs=extra)


def delete_file(storage_key: str) -> None:
    if settings.STORAGE_BACKEND == "local":
        (Path(settings.DOCUMENT_STORAGE_PATH).resolve() / storage_key).unlink(missing_ok=True)
    elif settings.STORAGE_BACKEND == "s3":
        _client().delete_object(Bucket=settings.S3_BUCKET, Key=storage_key)
    elif settings.STORAGE_BACKEND != "postgresql":
        raise RuntimeError("Unsupported document storage backend")


def open_file(storage_key: str):
    if settings.STORAGE_BACKEND == "local":
        return (Path(settings.DOCUMENT_STORAGE_PATH).resolve() / storage_key).open("rb")
    if settings.STORAGE_BACKEND == "s3":
        return _client().get_object(Bucket=settings.S3_BUCKET, Key=storage_key)["Body"]
    raise RuntimeError("PostgreSQL document bytes are read through StoredDocument.content")


def file_exists(storage_key: str) -> bool:
    if settings.STORAGE_BACKEND == "local":
        return (Path(settings.DOCUMENT_STORAGE_PATH).resolve() / storage_key).is_file()
    if settings.STORAGE_BACKEND == "s3":
        try:
            _client().head_object(Bucket=settings.S3_BUCKET, Key=storage_key)
            return True
        except Exception as exc:
            if getattr(exc, "response", {}).get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise
    return False
