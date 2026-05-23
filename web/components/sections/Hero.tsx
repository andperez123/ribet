import { ArrowRight, Play } from "lucide-react";
import { hero } from "@/lib/content/landing";
import { AlertBubble } from "@/components/ui/AlertBubble";
import { Button } from "@/components/ui/Button";
import { Container } from "@/components/ui/Container";
import { FrogHero } from "@/components/ui/FrogHero";

export function Hero() {
  return (
    <section className="pt-12 pb-0 md:pt-20">
      <Container>
        <div className="grid items-start gap-10 lg:grid-cols-2 lg:gap-16">
          <div className="max-w-xl">
            <h1 className="text-3xl font-semibold leading-snug tracking-tight text-ribet-text md:text-4xl lg:text-[2.75rem]">
              {hero.headline[0]}
              <br />
              {hero.headline[1]}{" "}
              <span className="text-ribet-green">{hero.highlightWord}</span>
            </h1>
            <p className="mt-5 whitespace-pre-line text-base leading-relaxed text-ribet-muted md:text-lg">
              {hero.subheadline}
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Button href="#upload">
                {hero.primaryCta}
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button href="/dashboard" variant="secondary">
                Open dashboard
              </Button>
              <Button href="#how-it-works" variant="ghost">
                <span className="flex h-8 w-8 items-center justify-center rounded-full border border-ribet-border">
                  <Play className="h-3.5 w-3.5 fill-ribet-text" />
                </span>
                {hero.secondaryCta}
              </Button>
            </div>
          </div>

          <div className="relative flex flex-col items-center lg:items-end">
            <div className="absolute top-0 right-4 z-10 lg:right-8">
              <AlertBubble text={hero.alert} />
            </div>
            <div className="mt-12 w-full lg:mt-8">
              <FrogHero />
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
