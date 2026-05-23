type BadgeProps = {
  children: React.ReactNode;
  variant?: "default" | "success" | "risk" | "muted";
  className?: string;
};

const variants = {
  default: "bg-rivet-green/15 text-rivet-green",
  success: "bg-rivet-green/15 text-rivet-green",
  risk: "bg-rivet-risk/15 text-rivet-risk",
  muted: "bg-rivet-border/50 text-rivet-muted",
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
