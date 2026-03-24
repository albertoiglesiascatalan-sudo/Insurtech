import { notFound } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { ArticleCard } from "@/components/articles/ArticleCard";
import { REGION_LABELS } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";

interface PageProps {
  params: Promise<{ region: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { region } = await params;
  const label = REGION_LABELS[region];
  if (!label) return {};
  return {
    title: `${label} InsurTech News`,
    description: `InsurTech news from ${label}.`,
  };
}

const REGION_DESCRIPTIONS: Record<string, string> = {
  US: "The largest insurtech market — from Silicon Valley unicorns to Bermuda re/insurers.",
  EU: "European regulation, open insurance, and a thriving startup ecosystem.",
  APAC: "Rapid digital adoption across China, Singapore, India, Australia and Southeast Asia.",
  LATAM: "Emerging insurtech markets with massive uninsured population opportunities.",
  MEA: "Takaful, microinsurance, and digital-first insurers in high-growth markets.",
  global: "Worldwide news impacting the entire insurtech industry.",
};

export default async function RegionPage({ params }: PageProps) {
  const { region } = await params;
  const label = REGION_LABELS[region];
  if (!label) notFound();

  const data = await api.articles.list({ region, page_size: "24" }).catch(() => ({ items: [], total: 0 }));

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link href="/news" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-6">
        <ArrowLeft className="w-4 h-4" /> All news
      </Link>

      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold text-slate-900">{label}</h1>
          <span className="bg-slate-100 text-slate-600 text-sm font-semibold px-3 py-1 rounded-full">
            {region}
          </span>
        </div>
        <p className="text-slate-600">{REGION_DESCRIPTIONS[region]}</p>
        <p className="text-slate-500 text-sm mt-1">{data.total} articles</p>
      </div>

      {data.items.length === 0 ? (
        <div className="text-center py-20 text-slate-400 bg-white rounded-2xl border">
          <p className="text-lg font-semibold mb-1">No articles for this region yet</p>
          <p className="text-sm">News is ingested every 30 minutes.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {data.items.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
