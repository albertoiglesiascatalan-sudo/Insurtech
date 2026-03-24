import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, format } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function timeAgo(date: string | null): string {
  if (!date) return "recently";
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function formatDate(date: string | null): string {
  if (!date) return "";
  return format(new Date(date), "MMM d, yyyy");
}

export const TOPIC_LABELS: Record<string, string> = {
  "embedded-insurance": "Embedded Insurance",
  "health-tech": "Health InsurTech",
  "auto-insurance": "Auto Insurance",
  "pc-innovation": "P&C Innovation",
  "climate-parametric": "Climate & Parametric",
  "regulatory-policy": "Regulatory & Policy",
  "funding-ma": "Funding & M&A",
  "partnerships": "Partnerships",
  "product-launches": "Product Launches",
  "ai-insurance": "AI in Insurance",
  "cyber-insurance": "Cyber Insurance",
  "life-insurance": "Life Insurance",
  "distribution": "Distribution",
  "claims-tech": "Claims Tech",
  "underwriting-tech": "Underwriting Tech",
};

export const REGION_LABELS: Record<string, string> = {
  US: "United States",
  EU: "Europe",
  APAC: "Asia Pacific",
  LATAM: "Latin America",
  MEA: "Middle East & Africa",
  global: "Global",
};

export const PROFILE_META: Record<string, { label: string; description: string; color: string }> = {
  investor: {
    label: "Investor",
    description: "Funding, M&A, valuations and market opportunities",
    color: "text-amber-600 bg-amber-50 border-amber-200",
  },
  founder: {
    label: "Founder",
    description: "Products, partnerships, regulatory and go-to-market",
    color: "text-blue-600 bg-blue-50 border-blue-200",
  },
  general: {
    label: "General",
    description: "Trends, consumer innovation and industry overview",
    color: "text-emerald-600 bg-emerald-50 border-emerald-200",
  },
};

export const SENTIMENT_COLORS: Record<string, string> = {
  positive: "text-green-600",
  neutral: "text-slate-500",
  negative: "text-red-500",
};
