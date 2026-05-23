import { howItWorks } from "@/lib/content/landing";
import { Container } from "@/components/ui/Container";

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 md:py-28">
      <Container>
        <h2 className="mb-16 text-center text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
          {howItWorks.title}
        </h2>
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {howItWorks.steps.map((item) => (
            <div key={item.step} className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-ribet-green/20 text-lg font-bold text-ribet-green">
                {item.step}
              </div>
              <p className="text-base font-medium text-ribet-text">
                {item.title}
              </p>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
