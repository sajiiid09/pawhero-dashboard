import { PageHeader } from "@/components/page-header";
import { PetForm } from "@/features/pets/pet-form";

export default async function EditPetRoute({
  params,
}: {
  params: Promise<{ petId: string }>;
}) {
  const { petId } = await params;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Pfoten-Held"
        title="Tierprofil bearbeiten"
        description="Aktualisiere Stammdaten, Gesundheitshinweise und Notfallrelevantes in einem Schritt."
      />
      <PetForm petId={petId} />
    </div>
  );
}
