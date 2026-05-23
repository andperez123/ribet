import { getDemoUrl } from "@/lib/config/env";
import { finalCta } from "@/lib/content/landing";
import { Button } from "@/components/ui/Button";
import { Container } from "@/components/ui/Container";

export function FinalCta() {
  return (
    <section id="demo" className="py-24 md:py-32">
      <Container>
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold leading-tight tracking-tight text-rivet-text md:text-4xl">
            {finalCta.headline[0]}
            <br />
            {finalCta.headline[1]}
          </h2>
          <p className="mt-6 text-lg text-rivet-muted">{finalCta.subtext}</p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Button href={getDemoUrl()} className="!px-8 !py-4 text-base">
              {finalCta.cta}
            </Button>
            <Button href="/dashboard" variant="secondary" className="!px-8 !py-4 text-base">
              Open dashboard
            </Button>
          </div>
        </div>
      </Container>
    </section>
  );
}
