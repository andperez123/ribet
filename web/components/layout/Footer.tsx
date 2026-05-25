import { footer } from "@/lib/content/landing";
import { Container } from "@/components/ui/Container";

export function Footer() {
  return (
    <footer className="border-t border-ribet-border py-12">
      <Container>
        <div className="flex flex-col items-center justify-between gap-4 text-center sm:flex-row sm:text-left">
          <p className="text-sm text-ribet-muted">{footer.tagline}</p>
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-ribet-muted">
            <a href="/legal/terms" className="hover:text-ribet-text">
              Terms
            </a>
            <a href="/legal/privacy" className="hover:text-ribet-text">
              Privacy
            </a>
            <span>{footer.copyright}</span>
          </div>
        </div>
      </Container>
    </footer>
  );
}
