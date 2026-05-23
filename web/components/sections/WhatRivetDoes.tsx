import { whatRivetDoes } from "@/lib/content/landing";
import { Container } from "@/components/ui/Container";

export function WhatRivetDoes() {
  return (
    <section className="py-20 md:py-28">
      <Container>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {whatRivetDoes.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.title}
                className="rounded-2xl border border-rivet-border bg-rivet-card p-8"
              >
                <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-rivet-green/15">
                  <Icon className="h-6 w-6 text-rivet-green" />
                </div>
                <h3 className="text-lg font-semibold text-rivet-text">
                  {card.title}
                </h3>
                <div className="mt-3 space-y-1">
                  {card.description.map((line) => (
                    <p key={line} className="text-sm text-rivet-muted">
                      {line}
                    </p>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </Container>
    </section>
  );
}
