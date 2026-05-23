import { trustBar } from "@/lib/content/landing";
import { Container } from "@/components/ui/Container";

export function TrustBar() {
  return (
    <section className="py-12 md:py-16">
      <Container>
        <p className="text-center text-sm font-medium tracking-wide text-rivet-muted uppercase">
          {trustBar.text}
        </p>
      </Container>
    </section>
  );
}
