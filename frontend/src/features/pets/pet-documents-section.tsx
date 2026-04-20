"use client";

import { motion } from "framer-motion";
import { FileText, Plus, Trash2, Download } from "lucide-react";
import { useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Field, inputClassName } from "@/components/ui/field";
import { FormSection } from "@/components/ui/form-section";
import { MotionSection } from "@/components/ui/motion";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useDeletePetDocumentMutation,
  useDownloadPetDocument,
  usePetDocumentsQuery,
  useUploadPetDocumentMutation,
} from "@/features/app/hooks";
import type { DocumentType, PetDocumentItem } from "@/features/app/types";

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  medical_record: "Krankenakte",
  vaccination_record: "Impfpass",
  insurance: "Versicherung",
  lab_result: "Laborbefund",
  other: "Sonstiges",
};

const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: "medical_record", label: "Krankenakte" },
  { value: "vaccination_record", label: "Impfpass" },
  { value: "insurance", label: "Versicherung" },
  { value: "lab_result", label: "Laborbefund" },
  { value: "other", label: "Sonstiges" },
];

const MAX_DOCUMENTS = 20;

type PetDocumentsSectionProps = {
  petId: string;
};

export function PetDocumentsSection({ petId }: PetDocumentsSectionProps) {
  const { data: documents, isLoading, error } = usePetDocumentsQuery(petId);
  const uploadMutation = useUploadPetDocumentMutation(petId);
  const deleteMutation = useDeletePetDocumentMutation(petId);
  const downloadMutation = useDownloadPetDocument(petId);

  const [title, setTitle] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType>("medical_record");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const docCount = documents?.length ?? 0;
  const canUpload = docCount < MAX_DOCUMENTS;

  function handleUpload() {
    const file = fileInputRef.current?.files?.[0];
    if (!file || !title.trim()) return;

    uploadMutation.mutate(
      { file, title: title.trim(), documentType },
      {
        onSuccess: () => {
          setTitle("");
          setDocumentType("medical_record");
          if (fileInputRef.current) {
            fileInputRef.current.value = "";
          }
        },
      },
    );
  }

  function handleDelete(docId: string) {
    deleteMutation.mutate(docId);
  }

  function handleDownload(docId: string) {
    downloadMutation.mutate(docId);
  }

  if (isLoading) {
    return (
      <div className="mt-6 space-y-4">
        <Skeleton className="h-14 w-full rounded-[28px]" />
        <Skeleton className="h-48 w-full rounded-[24px]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-6 rounded-[22px] border border-danger/20 bg-danger-soft px-5 py-4 text-sm font-semibold text-danger">
        Dokumente konnten nicht geladen werden.
      </div>
    );
  }

  return (
    <div className="mt-6">
      <MotionSection>
        <FormSection
          title="Dokumente"
          description="Vaccinationsscheine, Krankenakten und weitere Dokumente."
        >
          {/* Upload form */}
          <div className="space-y-4">
            {uploadMutation.error ? (
              <div className="rounded-[22px] border border-danger/20 bg-danger-soft px-5 py-4 text-sm font-semibold text-danger">
                {uploadMutation.error.message}
              </div>
            ) : null}

            {docCount >= MAX_DOCUMENTS - 2 && canUpload && (
              <p className="text-sm text-warning">
                {docCount} von {MAX_DOCUMENTS} Dokumenten hochgeladen.
              </p>
            )}

            {canUpload ? (
              <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto_auto]">
                <Field label="Titel">
                  <input
                    className={inputClassName()}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="z.B. Impfpass 2024"
                  />
                </Field>
                <Field label="Typ">
                  <select
                    className={inputClassName()}
                    value={documentType}
                    onChange={(e) => setDocumentType(e.target.value as DocumentType)}
                  >
                    {DOCUMENT_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </Field>
                <div className="flex items-end">
                  <label>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png,.webp"
                      className="sr-only"
                    />
                    <Button
                      type="button"
                      variant="secondary"
                      className="gap-2"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <FileText className="h-4 w-4" />
                      Datei waehlen
                    </Button>
                  </label>
                </div>
                <div className="flex items-end">
                  <Button
                    type="button"
                    className="gap-2"
                    disabled={uploadMutation.isPending || !title.trim()}
                    onClick={handleUpload}
                  >
                    <Plus className="h-4 w-4" />
                    {uploadMutation.isPending ? "Laedt..." : "Hochladen"}
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-text-muted">
                Maximale Anzahl an Dokumenten erreicht ({MAX_DOCUMENTS}).
              </p>
            )}

            <p className="text-xs text-text-muted">
              PDF, JPG, PNG oder WebP — max. 10 MB pro Datei.
            </p>
          </div>

          {/* Document list */}
          {!documents || documents.length === 0 ? (
            <EmptyState
              title="Keine Dokumente"
              description="Laden Sie Impfpaesse, Krankenakten oder andere Dokumente hoch."
            />
          ) : (
            <div className="mt-4 space-y-2">
              {documents.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  document={doc}
                  onDelete={handleDelete}
                  onDownload={handleDownload}
                  isDeleting={deleteMutation.isPending}
                />
              ))}
            </div>
          )}
        </FormSection>
      </MotionSection>
    </div>
  );
}

function DocumentRow({
  document,
  onDelete,
  onDownload,
  isDeleting,
}: {
  document: PetDocumentItem;
  onDelete: (id: string) => void;
  onDownload: (id: string) => void;
  isDeleting: boolean;
}) {
  const typeLabel =
    DOCUMENT_TYPE_LABELS[document.documentType as DocumentType] ??
    document.documentType;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="surface-card-muted flex items-center justify-between gap-3 rounded-[18px] px-4 py-3"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-semibold text-foreground">
            {document.title}
          </p>
          <Badge tone="default">{typeLabel}</Badge>
        </div>
        <p className="mt-0.5 text-xs text-text-muted">
          {document.originalFilename} · {formatFileSize(document.sizeBytes)} ·{" "}
          {formatDate(document.createdAt)}
        </p>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDownload(document.id)}
          aria-label={`Herunterladen: ${document.title}`}
        >
          <Download className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(document.id)}
          disabled={isDeleting}
          aria-label={`Loeschen: ${document.title}`}
        >
          <Trash2 className="h-4 w-4 text-danger" />
        </Button>
      </div>
    </motion.div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(isoString: string): string {
  try {
    return new Intl.DateTimeFormat("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    }).format(new Date(isoString));
  } catch {
    return isoString;
  }
}
