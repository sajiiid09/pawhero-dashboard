from pydantic import Field

from app.schemas.common import AppSchema


class PetDocumentDTO(AppSchema):
    id: str
    pet_id: str = Field(alias="petId")
    title: str
    document_type: str = Field(alias="documentType")
    original_filename: str = Field(alias="originalFilename")
    content_type: str = Field(alias="contentType")
    size_bytes: int = Field(alias="sizeBytes")
    is_public: bool = Field(alias="isPublic")
    created_at: str = Field(alias="createdAt")
