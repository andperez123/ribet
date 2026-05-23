export type SignalCard = {
  id: string;
  title: string;
  metric: string;
  severity?: "neutral" | "risk";
};

export const signalCards: SignalCard[] = [
  {
    id: "inventory",
    title: "Inventory adjustments",
    metric: "23% above normal",
    severity: "risk",
  },
  {
    id: "ar",
    title: "AR over 90 days",
    metric: "increased 11%",
    severity: "risk",
  },
  {
    id: "labor",
    title: "Labor efficiency declined",
    metric: "on Assembly Line 2",
    severity: "neutral",
  },
];

export const chatPreview = {
  question: "Why did margin decrease?",
  answer:
    "Inventory adjustments and overtime labor increased significantly this month.",
};
