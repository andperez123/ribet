type CardVariant = "default" | "hero" | "stat" | "locked";

type CardProps = {
  children: React.ReactNode;
  className?: string;
  variant?: CardVariant;
};

const VARIANT_CLASSES: Record<CardVariant, string> = {
  default: "rounded-2xl border border-ribet-border bg-ribet-card p-6 shadow-soft",
  hero: "rounded-3xl border border-ribet-ink-soft/40 bg-hero-gradient p-8 text-white shadow-hero md:p-10",
  stat: "rounded-xl border border-ribet-border bg-ribet-card px-4 py-3 shadow-soft",
  locked:
    "rounded-2xl border border-dashed border-ribet-border bg-ribet-bg/80 p-6 backdrop-blur-sm",
};

export function Card({
  children,
  className = "",
  variant = "default",
}: CardProps) {
  return (
    <div className={`${VARIANT_CLASSES[variant]} ${className}`}>
      {children}
    </div>
  );
}
