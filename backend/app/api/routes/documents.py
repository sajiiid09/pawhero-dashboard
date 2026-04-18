import logging

from fastapi import APIRouter, Form, HTTPException, UploadFile, status

from app.api.dependencies import DbSession, OwnerId
from app.repositories import documents as doc_repo
from app.repositories.pets import get_pet
from app.schemas.documents import PetDocumentDTO
from app.services import storage
from app.services.auth import generate_id
from app.services.documents import serialize_document

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pets"])

MAX_DOCUMENTS_PER_PET = 20


@router.get(
    "/{pet_id}/documents",
    response_model=list[PetDocumentDTO],
)
def list_pet_documents(pet_id: str, session: DbSession, owner_id: OwnerId) -> list[PetDocumentDTO]:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")
    docs = doc_repo.list_documents(session, owner_id, pet_id)
    return [serialize_document(d) for d in docs]


@router.post(
    "/{pet_id}/documents",
    response_model=PetDocumentDTO,
    status_code=status.HTTP_201_CREATED,
)
async def upload_pet_document(
    pet_id: str,
    file: UploadFile,
    title: str = Form(...),
    document_type: str = Form(...),
    session: DbSession = ...,  # type: ignore[assignment]
    owner_id: OwnerId = ...,  # type: ignore[assignment]
) -> PetDocumentDTO:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    count = doc_repo.count_documents(session, owner_id, pet_id)
    if count >= MAX_DOCUMENTS_PER_PET:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximal {MAX_DOCUMENTS_PER_PET} Dokumente pro Tier erlaubt.",
        )

    content_type = file.content_type or ""
    file_bytes = await file.read()
    file_size = len(file_bytes)

    try:
        storage.validate_document(content_type, file_size)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    doc_id = f"doc-{generate_id()}"

    try:
        storage_key = storage.upload_document(pet_id, file_bytes, content_type, doc_id)
    except Exception as exc:
        logger.exception("Document upload failed for pet %s", pet_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dokument konnte nicht hochgeladen werden. Bitte erneut versuchen.",
        ) from exc

    original_filename = file.filename or "unknown"

    doc = doc_repo.create_document(
        session=session,
        doc_id=doc_id,
        owner_id=owner_id,
        pet_id=pet_id,
        title=title,
        document_type=document_type,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=file_size,
        storage_key=storage_key,
    )
    session.commit()
    return serialize_document(doc)


@router.delete(
    "/{pet_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_pet_document(
    pet_id: str,
    document_id: str,
    session: DbSession,
    owner_id: OwnerId,
) -> None:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    doc = doc_repo.get_document(session, owner_id, document_id)
    if doc is None or doc.pet_id != pet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dokument nicht gefunden."
        )

    storage.delete_document(doc.storage_key)
    doc_repo.delete_document(session, owner_id, document_id)
    session.commit()


@router.get(
    "/{pet_id}/documents/{document_id}/download",
)
def download_pet_document(
    pet_id: str,
    document_id: str,
    session: DbSession,
    owner_id: OwnerId,
) -> dict:
    pet = get_pet(session, owner_id, pet_id)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found.")

    doc = doc_repo.get_document(session, owner_id, document_id)
    if doc is None or doc.pet_id != pet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dokument nicht gefunden."
        )

    try:
        signed_url = storage.create_download_url(doc.storage_key)
    except Exception as exc:
        logger.exception("Signed URL creation failed for doc %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Download-URL konnte nicht erstellt werden.",
        ) from exc

    return {"url": signed_url}
