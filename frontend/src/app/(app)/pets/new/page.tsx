import { PageHeader } from "@/components/page-header";
import { PetForm } from "@/features/pets/pet-form";

export default function NewPetRoute() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Pfoten-Held"
        title="Neuen Hund anlegen"
        description="Lege das Tierprofil mit medizinischen Hinweisen, Tierarzt und Pflegeinformationen an."
      />
      <PetForm />
    </div>
  );
}
