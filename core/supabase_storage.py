import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from supabase import create_client
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _client


def upload_png(path_in_bucket: str, png_bytes: bytes) -> str:
    """
    Upload raw PNG bytes to Supabase Storage.
    Returns the public URL of the uploaded file.
    Raises if Supabase is not configured or upload fails.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")

    client = _get_client()
    bucket = settings.SUPABASE_STORAGE_BUCKET

    try:
        client.storage.from_(bucket).upload(
            path=path_in_bucket,
            file=png_bytes,
            file_options={"content-type": "image/png", "upsert": "true"},
        )
    except Exception as e:
        raise RuntimeError(f"Supabase upload failed: {e}") from e

    public_url = client.storage.from_(bucket).get_public_url(path_in_bucket)
    return public_url


def delete_file(path_in_bucket: str) -> None:
    """Delete a file from Supabase Storage (best-effort, errors are logged not raised)."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return
    try:
        _get_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET).remove([path_in_bucket])
    except Exception as e:
        logger.warning("Supabase delete failed for %s: %s", path_in_bucket, e)
