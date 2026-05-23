type CardProps = {
  children: React.ReactNode;
  className?: string;
};

export function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-rivet-border bg-rivet-card p-6 ${className}`}
    >
      {children}
    </div>
  );
}
