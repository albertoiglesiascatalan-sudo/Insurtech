import { notFound } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { ArticleCard } from "@/components/articles/ArticleCard";
import { TOPIC_LABELS } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { slug } = await params;
  const label = TOPIC_LABELS[slug];
  if (!label) return {};
  return {
    title: `${label} News`,
    description: `Latest ${label} news from global insurtech sources.`,
  };
}

export default async function TopicPage({ params }: PageProps) {
  const { slug } = await params;
  const label = TOPIC_LABELS[slug];
  if (!label) notFound();

  const data = await api.articles.list({ topic: slug, page_size: "24" }).catch(() => ({ items: [], total: 0 }));

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link href="/topics" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-6">
        <ArrowLeft className="w-4 h-4" /> All topics
      </Link>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">{label}</h1>
          <p className="text-slate-500 mt-1">{data.total} articles</p>
        </div>
        <Link
          href={`/newsletter?topic=${slug}`}
          className="bg-brand text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-dark transition-colors"
        >
          Subscribe to {label} →
        </Link>
      </div>

      {data.items.length === 0 ? (
        <div className="text-center py-20 text-slate-400 bg-white rounded-2xl border">
          <p className="text-lg font-semibold mb-1">No articles yet for this topic</p>
          <p className="text-sm">Check back soon — we ingest new content every 30 minutes.</p>
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
