import { chatPreview, signalCards } from "@/lib/content/preview";
import { Container } from "@/components/ui/Container";

export function ProductPreview() {
  return (
    <section className="py-20 md:py-28">
      <Container>
        <h2 className="mb-4 text-center text-2xl font-semibold tracking-tight text-rivet-text md:text-3xl">
          Quiet intelligence.
          <br />
          <span className="text-rivet-muted text-xl font-normal md:text-2xl">
            Not another dashboard.
          </span>
        </h2>
        <p className="mb-12 text-center text-sm text-rivet-muted">
          Preview below is illustrative.{" "}
          <a href="/dashboard" className="font-medium text-rivet-green hover:underline">
            See live data on your dashboard
          </a>
          .
        </p>

        <div className="grid gap-4 md:grid-cols-3">
          {signalCards.map((card) => (
            <div
              key={card.id}
              className="rounded-2xl border border-rivet-border bg-rivet-card p-6"
            >
              <p className="text-sm text-rivet-muted">{card.title}</p>
              <p
                className={`mt-2 text-xl font-semibold ${
                  card.severity === "risk"
                    ? "text-rivet-risk"
                    : "text-rivet-text"
                }`}
              >
                {card.metric}
              </p>
            </div>
          ))}
        </div>

        <div className="mx-auto mt-10 max-w-2xl rounded-2xl border border-rivet-border bg-rivet-card p-6 md:p-8">
          <div className="rounded-xl bg-rivet-bg px-4 py-3 text-sm text-rivet-text">
            {chatPreview.question}
          </div>
          <div className="mt-4 flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-rivet-green/20 text-xs font-bold text-rivet-green">
              R
            </div>
            <p className="text-sm leading-relaxed text-rivet-muted">
              <span className="font-medium text-rivet-text">Ribet: </span>
              &ldquo;{chatPreview.answer}&rdquo;
            </p>
          </div>
        </div>
      </Container>
    </section>
  );
}
