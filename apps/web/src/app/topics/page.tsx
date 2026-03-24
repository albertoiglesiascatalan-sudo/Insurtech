import Link from "next/link";
import { TOPIC_LABELS } from "@/lib/utils";

export const metadata = {
  title: "Browse by Topic",
  description: "Explore insurtech news by topic: embedded insurance, AI, cyber, health, auto, climate and more.",
};

const TOPIC_DESCRIPTIONS: Record<string, string> = {
  "embedded-insurance": "Insurance embedded into products, platforms and services",
  "health-tech": "Digital health insurance, telemedicine and wellness tech",
  "auto-insurance": "Connected cars, usage-based and autonomous vehicle insurance",
  "pc-innovation": "Property & casualty digital transformation",
  "climate-parametric": "Climate risk, catastrophe bonds and parametric products",
  "regulatory-policy": "Global insurance regulation, compliance and policy updates",
  "funding-ma": "Funding rounds, acquisitions, mergers and valuations",
  "partnerships": "Insurer-startup partnerships and distribution deals",
  "product-launches": "New insurance products, features and market launches",
  "ai-insurance": "Machine learning, generative AI and automation in insurance",
  "cyber-insurance": "Cyber risk, data breach coverage and digital liability",
  "life-insurance": "Life, annuities and protection technology",
  "distribution": "Agents, brokers, direct-to-consumer and platform distribution",
  "claims-tech": "Claims automation, fraud detection and loss management",
  "underwriting-tech": "Risk models, pricing technology and underwriting automation",
};

export default function TopicsPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-slate-900 mb-2">Browse by Topic</h1>
      <p className="text-slate-600 mb-10">
        15 topic categories covering every corner of the insurtech industry.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(TOPIC_LABELS).map(([slug, label]) => (
          <Link
            key={slug}
            href={`/topics/${slug}`}
            className="bg-white border border-slate-200 hover:border-brand hover:shadow-md rounded-xl p-5 transition-all group"
          >
            <h2 className="font-bold text-slate-800 group-hover:text-brand mb-1.5 transition-colors">
              {label}
            </h2>
            <p className="text-sm text-slate-500 leading-relaxed">
              {TOPIC_DESCRIPTIONS[slug] || ""}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
