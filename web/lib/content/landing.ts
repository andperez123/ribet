import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BarChart3,
  Lightbulb,
  MessageCircle,
} from "lucide-react";

export const nav = {
  brand: "ribet",
  signIn: "Sign in",
  bookDemo: "Book a demo",
};

export const hero = {
  headline: ["Your AI", "operations", "manager."],
  highlightWord: "manager.",
  subheadline: "Ribet watches your operation\nso you can run it.",
  primaryCta: "See Ribet in action",
  secondaryCta: "How it works",
  alert: "3 issues found",
};

export const trustBar = {
  text: "Built for manufacturers.",
};

export const uploadSection = {
  headline: ["Upload by sector.", "Unlock logistics."],
  boxTitle: "Upload your ERP exports",
  boxSubtitle: "CSV, Excel, or PDF",
  helper: "No ERP integrations required.",
  accepted: ".csv,.xlsx,.xls,.pdf",
};

export type FeatureCard = {
  title: string;
  description: string[];
  icon: LucideIcon;
};

export const whatRibetDoes: FeatureCard[] = [
  {
    title: "Detect issues",
    description: [
      "Duplicate invoices.",
      "Inventory mismatches.",
      "Margin leaks.",
    ],
    icon: Activity,
  },
  {
    title: "Understand operations",
    description: [
      "See what is slowing",
      "cash flow and efficiency.",
    ],
    icon: BarChart3,
  },
  {
    title: "Get recommendations",
    description: [
      "Ribet explains",
      "what needs attention.",
    ],
    icon: Lightbulb,
  },
  {
    title: "Ask questions",
    description: [
      '"Which jobs lost money?"',
      '"What changed margins?"',
    ],
    icon: MessageCircle,
  },
];

export const howItWorks = {
  title: "How it works",
  steps: [
    { step: 1, title: "Upload ERP exports" },
    { step: 2, title: "Ribet normalizes your data" },
    { step: 3, title: "Ribet finds operational risks" },
    { step: 4, title: "Get daily operational intelligence" },
  ],
};

export const finalCta = {
  headline: ["Know what's happening", "inside your operation."],
  subtext:
    "Ribet monitors financial and operational data to detect issues before they become losses.",
  cta: "Book a demo",
};

export const footer = {
  tagline: "Ribet watches your operation.",
  copyright: `© ${new Date().getFullYear()} Ribet`,
};
