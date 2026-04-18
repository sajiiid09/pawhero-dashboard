from app.db.models import PetDocument
from app.schemas.documents import PetDocumentDTO


def serialize_document(doc: PetDocument) -> PetDocumentDTO:
    return PetDocumentDTO.model_validate(
        {
            "id": doc.id,
            "pet_id": doc.pet_id,
            "title": doc.title,
            "document_type": doc.document_type,
            "original_filename": doc.original_filename,
            "content_type": doc.content_type,
            "size_bytes": doc.size_bytes,
            "is_public": doc.is_public,
            "created_at": doc.created_at.isoformat(),
        }
    )
