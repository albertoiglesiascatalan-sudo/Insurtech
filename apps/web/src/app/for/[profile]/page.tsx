import { notFound } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { ArticleCard } from "@/components/articles/ArticleCard";
import { PROFILE_META } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";

interface PageProps {
  params: Promise<{ profile: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { profile } = await params;
  const meta = PROFILE_META[profile];
  if (!meta) return {};
  return {
    title: `InsurTech for ${meta.label}s`,
    description: meta.description,
  };
}

const PROFILE_COPY = {
  investor: {
    emoji: "📈",
    headline: "InsurTech Intelligence for Investors",
    subtitle: "Funding rounds, M&A activity, valuations, market sizing and competitive intelligence — curated for VCs, PEs and strategic investors.",
    highlights: ["Funding & M&A news", "Market opportunities", "Competitive dynamics", "Regulatory impact on investments"],
  },
  founder: {
    emoji: "🚀",
    headline: "InsurTech Intelligence for Founders",
    subtitle: "Product launches, technology innovations, partnership strategies and regulatory updates — curated for insurtech builders.",
    highlights: ["Product launches", "Tech innovations", "Distribution strategies", "Regulatory updates"],
  },
  general: {
    emoji: "🌐",
    headline: "InsurTech Intelligence — General Edition",
    subtitle: "The biggest trends, consumer innovations and industry stories reshaping insurance — for professionals and curious minds alike.",
    highlights: ["Macro trends", "Consumer innovation", "Industry news", "Expert analysis"],
  },
};

export default async function ProfilePage({ params }: PageProps) {
  const { profile } = await params;
  const meta = PROFILE_META[profile];
  if (!meta) notFound();

  const copy = PROFILE_COPY[profile as keyof typeof PROFILE_COPY];
  const data = await api.articles.list({ profile, page_size: "24" }).catch(() => ({ items: [], total: 0 }));

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link href="/news" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-6">
        <ArrowLeft className="w-4 h-4" /> All news
      </Link>

      {/* Profile hero */}
      <div className="bg-gradient-to-br from-slate-900 to-navy rounded-3xl p-8 mb-10 text-white">
        <div className="text-4xl mb-4">{copy.emoji}</div>
        <h1 className="text-3xl font-bold mb-3">{copy.headline}</h1>
        <p className="text-slate-300 max-w-2xl mb-6">{copy.subtitle}</p>
        <div className="flex flex-wrap gap-2 mb-6">
          {copy.highlights.map((h) => (
            <span key={h} className="bg-white/10 text-white text-sm px-3 py-1 rounded-full">{h}</span>
          ))}
        </div>
        <Link
          href={`/newsletter?profile=${profile}`}
          className="inline-flex bg-brand hover:bg-brand-dark text-white font-bold px-6 py-2.5 rounded-xl transition-colors"
        >
          Get the {meta.label} newsletter →
        </Link>
      </div>

      {/* Other profiles */}
      <div className="flex gap-2 mb-8">
        {Object.entries(PROFILE_META)
          .filter(([k]) => k !== profile)
          .map(([k, v]) => (
            <Link
              key={k}
              href={`/for/${k}`}
              className={`text-sm border rounded-full px-4 py-1.5 font-medium transition-colors ${v.color}`}
            >
              Switch to {v.label} edition
            </Link>
          ))}
      </div>

      <p className="text-slate-500 text-sm mb-6">{data.total} articles for {meta.label}s</p>

      {data.items.length === 0 ? (
        <div className="text-center py-20 text-slate-400 bg-white rounded-2xl border">
          <p className="text-lg font-semibold mb-1">No articles yet</p>
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
