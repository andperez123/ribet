import { ChevronRight } from "lucide-react";

export function AlertBubble({ text }: { text: string }) {
  return (
    <div className="animate-float flex items-center gap-2 rounded-full border border-ribet-border bg-ribet-card px-4 py-2.5 text-sm font-medium text-ribet-text shadow-sm">
      <span className="h-2 w-2 shrink-0 rounded-full bg-ribet-green" />
      <span>{text}</span>
      <ChevronRight className="h-4 w-4 text-ribet-muted" />
    </div>
  );
}
