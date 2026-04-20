"""Supabase Storage abstraction for pet images and documents."""

from __future__ import annotations

import logging
import uuid

from supabase import Client, create_client

from app.core.config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024  # 10 MB

IMAGES_BUCKET = "pet-images"
DOCUMENTS_BUCKET = "pet-documents"
DOCUMENT_SIGNED_URL_EXPIRES_SEC = 900


def _get_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_secret_key)


def _get_public_url_base() -> str:
    """Return the base URL for the public images bucket."""
    settings = get_settings()
    return f"{settings.supabase_url}/storage/v1/object/public/{IMAGES_BUCKET}"


def validate_image(content_type: str, size: int) -> None:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(
            f"Ungueltiger Dateityp. Erlaubt: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}."
        )
    if size > MAX_IMAGE_BYTES:
        raise ValueError(f"Bild zu gross. Maximal {MAX_IMAGE_BYTES // (1024 * 1024)} MB erlaubt.")


def validate_document(content_type: str, size: int) -> None:
    if content_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError(
            f"Ungueltiger Dateityp. Erlaubt: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}."
        )
    if size > MAX_DOCUMENT_BYTES:
        raise ValueError(
            f"Dokument zu gross. Maximal {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB erlaubt."
        )


def upload_image(pet_id: str, file_bytes: bytes, content_type: str) -> str:
    """Upload an image to the public pet-images bucket. Returns the public CDN URL."""
    ext = ALLOWED_IMAGE_TYPES[content_type]
    storage_key = f"pets/{pet_id}/{uuid.uuid4().hex[:16]}{ext}"

    client = _get_client()
    client.storage.from_(IMAGES_BUCKET).upload(
        path=storage_key,
        file=file_bytes,
        file_options={"content-type": content_type},
    )

    public_url = f"{_get_public_url_base()}/{storage_key}"
    logger.info("Uploaded image to %s", public_url)
    return public_url


def delete_image(image_url: str) -> None:
    """Delete an image from the public bucket by extracting the key from its URL."""
    base = _get_public_url_base() + "/"
    if not image_url.startswith(base):
        return
    storage_key = image_url[len(base) :]
    _delete_from_bucket(IMAGES_BUCKET, storage_key)


def upload_document(pet_id: str, file_bytes: bytes, content_type: str, doc_id: str) -> str:
    """Upload a document to the private pet-documents bucket. Returns the storage key."""
    ext = ALLOWED_DOCUMENT_TYPES[content_type]
    storage_key = f"pets/{pet_id}/{doc_id}{ext}"

    client = _get_client()
    client.storage.from_(DOCUMENTS_BUCKET).upload(
        path=storage_key,
        file=file_bytes,
        file_options={"content-type": content_type},
    )

    logger.info("Uploaded document to %s", storage_key)
    return storage_key


def delete_document(storage_key: str) -> None:
    """Delete a document from the private bucket."""
    _delete_from_bucket(DOCUMENTS_BUCKET, storage_key)


def create_download_url(
    storage_key: str,
    expires_sec: int = DOCUMENT_SIGNED_URL_EXPIRES_SEC,
) -> str:
    """Create a signed URL for downloading a private document."""
    client = _get_client()
    response = client.storage.from_(DOCUMENTS_BUCKET).create_signed_url(storage_key, expires_sec)
    signed_url: str = response.get("signedURL", "") if isinstance(response, dict) else str(response)
    logger.info("Created signed document URL (expires in %ds)", expires_sec)
    return signed_url


def _delete_from_bucket(bucket: str, storage_key: str) -> None:
    try:
        client = _get_client()
        client.storage.from_(bucket).remove([storage_key])
        logger.info("Deleted %s from bucket %s", storage_key, bucket)
    except Exception:
        logger.warning("Failed to delete %s from bucket %s", storage_key, bucket, exc_info=True)
