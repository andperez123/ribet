import type { LucideIcon } from "lucide-react";
import { Activity, BarChart3, Lightbulb } from "lucide-react";

export const nav = {
  brand: "ribet",
  signIn: "Sign in",
  bookDemo: "Book a demo",
};

export const hero = {
  headline: ["Operational health,", "from your ERP", "exports."],
  highlightWord: "exports.",
  subheadline:
    "Ribet turns AR, AP, GL, and inventory exports into an operational health report for SMB manufacturers.",
  primaryCta: "Try demo data",
  secondaryCta: "How it works",
  alert: "3 issues found",
};

export const trustBar = {
  text: "Built for manufacturers.",
};

export const uploadSection = {
  headline: ["Upload by sector.", "Unlock logistics."],
  boxTitle: "Upload your ERP exports",
  boxSubtitle: "CSV or Excel",
  helper: "No ERP integrations required.",
  accepted: ".csv,.xlsx",
};

export type FeatureCard = {
  title: string;
  description: string[];
  icon: LucideIcon;
};

export const whatRibetDoes: FeatureCard[] = [
  {
    title: "Detect cash and inventory risks",
    description: [
      "AR aging spikes.",
      "Vendor concentration.",
      "Inventory adjustments.",
    ],
    icon: Activity,
  },
  {
    title: "Score operational health",
    description: [
      "A single health score",
      "with component breakdowns.",
    ],
    icon: BarChart3,
  },
  {
    title: "Explain what to do next",
    description: [
      "Prioritized findings",
      "with suggested actions.",
    ],
    icon: Lightbulb,
  },
];

export const howItWorks = {
  title: "How it works",
  steps: [
    { step: 1, title: "Upload ERP exports" },
    { step: 2, title: "Ribet normalizes your data" },
    { step: 3, title: "Ribet finds operational risks" },
    { step: 4, title: "Get a weekly operational health report" },
  ],
};

export const finalCta = {
  headline: ["Know what's happening", "inside your operation."],
  subtext:
    "Ribet analyzes ERP exports and surfaces operational risks before they become losses.",
  cta: "Book a demo",
};

export const footer = {
  tagline: "Operational intelligence from ERP exports.",
  copyright: `© ${new Date().getFullYear()} Ribet`,
};
