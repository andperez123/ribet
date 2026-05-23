import { footer } from "@/lib/content/landing";
import { Container } from "@/components/ui/Container";

export function Footer() {
  return (
    <footer className="border-t border-rivet-border py-12">
      <Container>
        <div className="flex flex-col items-center justify-between gap-4 text-center sm:flex-row sm:text-left">
          <p className="text-sm text-rivet-muted">{footer.tagline}</p>
          <p className="text-xs text-rivet-muted">{footer.copyright}</p>
        </div>
      </Container>
    </footer>
  );
}
