from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.db.models import PetDocument


def list_documents(session: Session, owner_id: str, pet_id: str) -> list[PetDocument]:
    statement: Select[tuple[PetDocument]] = (
        select(PetDocument)
        .where(PetDocument.owner_id == owner_id, PetDocument.pet_id == pet_id)
        .order_by(desc(PetDocument.created_at))
    )
    return list(session.scalars(statement))


def get_document(session: Session, owner_id: str, document_id: str) -> PetDocument | None:
    statement = select(PetDocument).where(
        PetDocument.owner_id == owner_id, PetDocument.id == document_id
    )
    return session.scalar(statement)


def count_documents(session: Session, owner_id: str, pet_id: str) -> int:
    statement = (
        select(func.count())
        .select_from(PetDocument)
        .where(PetDocument.owner_id == owner_id, PetDocument.pet_id == pet_id)
    )
    result = session.scalar(statement)
    return result or 0


def create_document(
    session: Session,
    doc_id: str,
    owner_id: str,
    pet_id: str,
    title: str,
    document_type: str,
    original_filename: str,
    content_type: str,
    size_bytes: int,
    storage_key: str,
    is_public: bool = False,
) -> PetDocument:
    doc = PetDocument(
        id=doc_id,
        owner_id=owner_id,
        pet_id=pet_id,
        title=title,
        document_type=document_type,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=size_bytes,
        storage_key=storage_key,
        is_public=is_public,
    )
    session.add(doc)
    session.flush()
    return doc


def delete_document(session: Session, owner_id: str, document_id: str) -> bool:
    doc = get_document(session, owner_id, document_id)
    if doc is None:
        return False
    session.delete(doc)
    session.flush()
    return True
