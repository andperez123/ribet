type BadgeProps = {
  children: React.ReactNode;
  variant?: "default" | "success" | "risk" | "muted";
  className?: string;
};

const variants = {
  default: "bg-ribet-green/15 text-ribet-green",
  success: "bg-ribet-green/15 text-ribet-green",
  risk: "bg-ribet-risk/15 text-ribet-risk",
  muted: "bg-ribet-border/50 text-ribet-muted",
};

export function Badge({
  children,
  variant = "default",
  className = "",
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
