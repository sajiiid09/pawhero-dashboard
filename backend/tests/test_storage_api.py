"""Tests for pet image upload, document CRUD, and storage integration."""

from __future__ import annotations

import io
from unittest.mock import Mock, patch

from fastapi import status

from app.services import storage as storage_module


def _create_test_pet(client, auth_headers) -> str:
    """Create a fresh test pet and return its ID."""
    response = client.post(
        "/pets",
        headers=auth_headers,
        json={
            "name": "StorageTestDog",
            "breed": "Mixed",
            "ageYears": 3,
            "weightKg": 10,
            "chipNumber": "PH-STORAGETEST",
            "address": "Teststrasse 1, Berlin",
            "imageUrl": None,
            "medicalProfile": {
                "preExistingConditions": "Keine",
                "allergies": "Keine",
                "medications": "Keine",
                "vaccinationStatus": "Aktuell",
                "insurance": "Keine",
            },
            "veterinarian": {"name": "Test Vet", "phone": "+49 30 000"},
            "feedingNotes": "Test.",
            "specialNeeds": "Keine.",
            "spareKeyLocation": "Keiner.",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


# --- Image upload tests ---


def test_upload_pet_image_success(client, auth_headers):
    """Upload a JPEG image for a seeded pet and verify imageUrl is updated."""
    pet_id = "pet-bello"

    with (
        patch.object(
            storage_module, "upload_image", return_value="https://cdn.example.com/test.jpg"
        ) as mock_upload,
        patch.object(storage_module, "delete_image"),
    ):
        response = client.post(
            f"/pets/{pet_id}/image",
            headers=auth_headers,
            files={
                "file": ("photo.jpg", io.BytesIO(b"\xff\xd8\xff\xe0fake_jpeg_data"), "image/jpeg")
            },
        )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["imageUrl"] == "https://cdn.example.com/test.jpg"
    mock_upload.assert_called_once()


def test_upload_pet_image_invalid_type(client, auth_headers):
    """Reject a non-image file type."""
    pet_id = "pet-bello"

    response = client.post(
        f"/pets/{pet_id}/image",
        headers=auth_headers,
        files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_upload_pet_image_wrong_owner(client, auth_headers):
    """Return 404 when uploading image for a non-existent or non-owned pet."""
    response = client.post(
        "/pets/nonexistent-pet/image",
        headers=auth_headers,
        files={"file": ("photo.jpg", io.BytesIO(b"\xff\xd8\xff\xe0data"), "image/jpeg")},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_upload_pet_image_replaces_old(client, auth_headers):
    """When re-uploading, the old CDN image should be deleted."""
    # Create a fresh pet to avoid DB state from other tests
    create_resp = client.post(
        "/pets",
        headers=auth_headers,
        json={
            "name": "ReplaceDog",
            "breed": "Mixed",
            "ageYears": 3,
            "weightKg": 10,
            "chipNumber": "PH-REPLACE",
            "address": "Teststrasse 1, Berlin",
            "imageUrl": None,
            "medicalProfile": {
                "preExistingConditions": "Keine",
                "allergies": "Keine",
                "medications": "Keine",
                "vaccinationStatus": "Aktuell",
                "insurance": "Keine",
            },
            "veterinarian": {"name": "Test Vet", "phone": "+49 30 000"},
            "feedingNotes": "Test.",
            "specialNeeds": "Keine.",
            "spareKeyLocation": "Keiner.",
        },
    )
    pet_id = create_resp.json()["id"]

    with (
        patch.object(
            storage_module,
            "upload_image",
            side_effect=[
                "https://cdn.example.com/first.jpg",
                "https://cdn.example.com/second.jpg",
            ],
        ),
        patch.object(storage_module, "delete_image") as mock_delete,
    ):
        # First upload
        client.post(
            f"/pets/{pet_id}/image",
            headers=auth_headers,
            files={"file": ("a.jpg", io.BytesIO(b"\xff\xd8data1"), "image/jpeg")},
        )

        # Second upload — should trigger delete of first image
        client.post(
            f"/pets/{pet_id}/image",
            headers=auth_headers,
            files={"file": ("b.jpg", io.BytesIO(b"\xff\xd8data2"), "image/jpeg")},
        )

    mock_delete.assert_called_once_with("https://cdn.example.com/first.jpg")


# --- Document CRUD tests ---


def test_list_documents_empty(client, auth_headers):
    """Return an empty list when no documents exist for a pet."""
    pet_id = "pet-bello"
    response = client.get(f"/pets/{pet_id}/documents", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_upload_document_success(client, auth_headers):
    """Upload a PDF document and verify metadata is returned."""
    pet_id = "pet-bello"

    with patch.object(
        storage_module, "upload_document", return_value="pets/pet-bello/doc-test.pdf"
    ):
        response = client.post(
            f"/pets/{pet_id}/documents",
            headers=auth_headers,
            files={
                "file": ("impfpass.pdf", io.BytesIO(b"%PDF-1.4 fake content"), "application/pdf")
            },
            data={"title": "Impfpass 2024", "document_type": "vaccination_record"},
        )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["title"] == "Impfpass 2024"
    assert body["documentType"] == "vaccination_record"
    assert body["contentType"] == "application/pdf"
    assert body["sizeBytes"] > 0
    assert body["originalFilename"] == "impfpass.pdf"


def test_upload_document_invalid_type(client, auth_headers):
    """Reject a non-allowed document type."""
    pet_id = "pet-bello"

    response = client.post(
        f"/pets/{pet_id}/documents",
        headers=auth_headers,
        files={"file": ("malware.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        data={"title": "Bad file", "document_type": "other"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_upload_document_wrong_owner(client, auth_headers):
    """Return 404 when uploading document for a non-existent pet."""
    response = client.post(
        "/pets/nonexistent/documents",
        headers=auth_headers,
        files={"file": ("test.pdf", io.BytesIO(b"data"), "application/pdf")},
        data={"title": "Test", "document_type": "other"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_documents_returns_uploaded(client, auth_headers):
    """List documents returns the documents uploaded for a pet."""
    # Create a fresh pet to ensure no documents from other tests
    create_resp = client.post(
        "/pets",
        headers=auth_headers,
        json={
            "name": "DocDog",
            "breed": "Mixed",
            "ageYears": 2,
            "weightKg": 8,
            "chipNumber": "PH-DOCLIST",
            "address": "Teststrasse 1, Berlin",
            "imageUrl": None,
            "medicalProfile": {
                "preExistingConditions": "Keine",
                "allergies": "Keine",
                "medications": "Keine",
                "vaccinationStatus": "Aktuell",
                "insurance": "Keine",
            },
            "veterinarian": {"name": "Test Vet", "phone": "+49 30 000"},
            "feedingNotes": "Test.",
            "specialNeeds": "Keine.",
            "spareKeyLocation": "Keiner.",
        },
    )
    pet_id = create_resp.json()["id"]

    with patch.object(
        storage_module, "upload_document", return_value=f"pets/{pet_id}/doc-test.pdf"
    ):
        # Upload a document
        client.post(
            f"/pets/{pet_id}/documents",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"title": "Test Doc", "document_type": "other"},
        )

    response = client.get(f"/pets/{pet_id}/documents", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["title"] == "Test Doc"


def test_delete_document_success(client, auth_headers):
    """Delete a document removes metadata and calls storage delete."""
    # Use a fresh pet to avoid DB state from other tests
    pet_id = _create_test_pet(client, auth_headers)

    with patch.object(storage_module, "upload_document", return_value=f"pets/{pet_id}/doc-del.pdf"):
        upload_resp = client.post(
            f"/pets/{pet_id}/documents",
            headers=auth_headers,
            files={"file": ("del.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"title": "To Delete", "document_type": "other"},
        )

    doc_id = upload_resp.json()["id"]

    with patch.object(storage_module, "delete_document") as mock_delete:
        response = client.delete(
            f"/pets/{pet_id}/documents/{doc_id}",
            headers=auth_headers,
        )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_delete.assert_called_once()

    # Verify it's gone from the list
    list_resp = client.get(f"/pets/{pet_id}/documents", headers=auth_headers)
    assert list_resp.json() == []


def test_delete_document_wrong_owner(client, auth_headers):
    """Return 404 when deleting a document that doesn't belong to the owner."""
    response = client.delete(
        "/pets/pet-bello/documents/nonexistent-doc",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_download_document_returns_signed_url(client, auth_headers):
    """Download endpoint returns a signed URL for the document."""
    pet_id = _create_test_pet(client, auth_headers)

    with patch.object(storage_module, "upload_document", return_value=f"pets/{pet_id}/doc-dl.pdf"):
        upload_resp = client.post(
            f"/pets/{pet_id}/documents",
            headers=auth_headers,
            files={"file": ("dl.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"title": "Download Test", "document_type": "medical_record"},
        )

    doc_id = upload_resp.json()["id"]

    with patch.object(
        storage_module,
        "create_download_url",
        return_value="https://cdn.example.com/signed?token=abc",
    ):
        response = client.get(
            f"/pets/{pet_id}/documents/{doc_id}/download",
            headers=auth_headers,
        )

    assert response.status_code == status.HTTP_200_OK
    assert "url" in response.json()


def test_delete_pet_cleans_up_storage(client, auth_headers):
    """Deleting a pet also cleans up image and document storage."""
    pet_id = _create_test_pet(client, auth_headers)

    with (
        patch.object(
            storage_module, "upload_image", return_value="https://cdn.example.com/img.jpg"
        ),
        patch.object(storage_module, "delete_image") as mock_del_image,
    ):
        # Upload an image first
        client.post(
            f"/pets/{pet_id}/image",
            headers=auth_headers,
            files={"file": ("photo.jpg", io.BytesIO(b"\xff\xd8data"), "image/jpeg")},
        )

    with patch.object(storage_module, "upload_document", return_value=f"pets/{pet_id}/doc.pdf"):
        client.post(
            f"/pets/{pet_id}/documents",
            headers=auth_headers,
            files={"file": ("test.pdf", io.BytesIO(b"data"), "application/pdf")},
            data={"title": "Doc", "document_type": "other"},
        )

    # Delete the pet — should clean up both image and document
    with (
        patch.object(storage_module, "delete_image") as mock_del_image,
        patch.object(storage_module, "delete_document") as mock_del_doc,
    ):
        response = client.delete(f"/pets/{pet_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_del_image.assert_called_once()
    mock_del_doc.assert_called_once()


# --- Storage service unit tests ---


def test_upload_image_passes_raw_bytes_to_supabase():
    """Supabase storage3 expects raw bytes, not BytesIO."""
    file_bytes = b"\xff\xd8image-data"
    upload = Mock()
    bucket = Mock(upload=upload)
    storage = Mock()
    storage.from_.return_value = bucket
    client = Mock(storage=storage)

    with (
        patch.object(storage_module, "_get_client", return_value=client),
        patch.object(
            storage_module,
            "_get_public_url_base",
            return_value="https://cdn.example.com/storage/v1/object/public/pet-images",
        ),
    ):
        public_url = storage_module.upload_image("pet-123", file_bytes, "image/jpeg")

    storage.from_.assert_called_once_with(storage_module.IMAGES_BUCKET)
    upload.assert_called_once()
    upload_kwargs = upload.call_args.kwargs
    assert upload_kwargs["file"] == file_bytes
    assert isinstance(upload_kwargs["file"], bytes)
    assert upload_kwargs["file_options"] == {"content-type": "image/jpeg"}
    assert upload_kwargs["path"].startswith("pets/pet-123/")
    assert upload_kwargs["path"].endswith(".jpg")
    assert public_url == (
        "https://cdn.example.com/storage/v1/object/public/pet-images/"
        f"{upload_kwargs['path']}"
    )


def test_upload_document_passes_raw_bytes_to_supabase():
    """Document uploads must also pass raw bytes and preserve the content type."""
    file_bytes = b"%PDF-1.4 document-data"
    upload = Mock()
    bucket = Mock(upload=upload)
    storage = Mock()
    storage.from_.return_value = bucket
    client = Mock(storage=storage)

    with patch.object(storage_module, "_get_client", return_value=client):
        storage_key = storage_module.upload_document(
            "pet-123",
            file_bytes,
            "application/pdf",
            "doc-456",
        )

    storage.from_.assert_called_once_with(storage_module.DOCUMENTS_BUCKET)
    upload.assert_called_once_with(
        path="pets/pet-123/doc-456.pdf",
        file=file_bytes,
        file_options={"content-type": "application/pdf"},
    )
    assert storage_key == "pets/pet-123/doc-456.pdf"


def test_validate_image_accepts_jpeg():
    storage_module.validate_image("image/jpeg", 1024)  # Should not raise


def test_validate_image_rejects_bad_type():
    import pytest

    with pytest.raises(ValueError, match="Ungueltiger Dateityp"):
        storage_module.validate_image("text/plain", 1024)


def test_validate_image_rejects_oversized():
    import pytest

    with pytest.raises(ValueError, match="zu gross"):
        storage_module.validate_image("image/jpeg", 6 * 1024 * 1024)


def test_validate_document_accepts_pdf():
    storage_module.validate_document("application/pdf", 1024)  # Should not raise


def test_validate_document_rejects_bad_type():
    import pytest

    with pytest.raises(ValueError, match="Ungueltiger Dateityp"):
        storage_module.validate_document("application/exe", 1024)


def test_validate_document_rejects_oversized():
    import pytest

    with pytest.raises(ValueError, match="zu gross"):
        storage_module.validate_document("application/pdf", 11 * 1024 * 1024)
