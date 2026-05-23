import { uploadSection } from "@/lib/content/landing";
import { Container } from "@/components/ui/Container";
import { SectorUploadFlow } from "@/features/upload/SectorUploadFlow";

export function UploadSection() {
  return (
    <section id="upload" className="relative -mt-8 pb-8 md:-mt-16 md:pb-16">
      <Container>
        <h2 className="mb-8 text-center text-2xl font-semibold tracking-tight text-rivet-text md:text-3xl">
          {uploadSection.headline[0]}
          <br />
          <span className="text-rivet-green">{uploadSection.headline[1]}</span>
        </h2>
        <SectorUploadFlow />
      </Container>
    </section>
  );
}
