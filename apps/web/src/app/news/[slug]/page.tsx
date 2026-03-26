import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { ExternalLink, ArrowLeft, Calendar, User, TrendingUp, TrendingDown, Minus, Shield } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate, TOPIC_LABELS, REGION_LABELS, SENTIMENT_COLORS } from "@/lib/utils";

const SENTIMENT_ICONS = {
  positive: TrendingUp,
  neutral: Minus,
  negative: TrendingDown,
};

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { slug } = await params;
  try {
    const article = await api.articles.get(slug);
    return {
      title: article.title,
      description: article.summary_ai || undefined,
      openGraph: { title: article.title, description: article.summary_ai || undefined, images: article.image_url ? [article.image_url] : [] },
    };
  } catch {
    return { title: "Article Not Found" };
  }
}

export default async function ArticlePage({ params }: PageProps) {
  const { slug } = await params;
  let article;
  try {
    article = await api.articles.get(slug);
  } catch {
    notFound();
  }

  const SentimentIcon = article.sentiment
    ? SENTIMENT_ICONS[article.sentiment as keyof typeof SENTIMENT_ICONS] || Minus
    : null;

  const sentimentLabel: Record<string, string> = {
    positive: "Positive outlook",
    neutral: "Neutral",
    negative: "Negative / cautionary",
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Back */}
      <Link
        href="/news"
        className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to news
      </Link>

      <article className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        {/* Hero image */}
        {article.image_url && (
          <div className="relative h-64 sm:h-96 bg-slate-100">
            <Image
              src={article.image_url}
              alt={article.title}
              fill
              className="object-cover"
              unoptimized
            />
          </div>
        )}

        <div className="p-6 sm:p-10">
          {/* Topics */}
          {article.topics.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-5">
              {article.topics.map((t) => (
                <Link
                  key={t}
                  href={`/topics/${t}`}
                  className="text-xs font-semibold text-brand bg-brand/10 px-3 py-1 rounded-full hover:bg-brand hover:text-white transition-colors"
                >
                  {TOPIC_LABELS[t] || t}
                </Link>
              ))}
            </div>
          )}

          {/* Title */}
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 leading-tight mb-5">
            {article.title}
          </h1>

          {/* Meta row */}
          <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500 pb-6 border-b border-slate-100 mb-6">
            <span className="font-semibold text-slate-700">{article.source.name}</span>
            {article.author && (
              <span className="flex items-center gap-1">
                <User className="w-3.5 h-3.5" /> {article.author}
              </span>
            )}
            {article.published_at && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" /> {formatDate(article.published_at)}
              </span>
            )}
            {SentimentIcon && article.sentiment && (
              <span className={`flex items-center gap-1 font-medium ${SENTIMENT_COLORS[article.sentiment]}`}>
                <SentimentIcon className="w-3.5 h-3.5" />
                {sentimentLabel[article.sentiment]}
              </span>
            )}
            {article.regions.map((r) => (
              <Link key={r} href={`/regions/${r}`} className="bg-slate-100 px-2 py-0.5 rounded text-xs font-medium hover:bg-slate-200 transition-colors">
                {REGION_LABELS[r] || r}
              </Link>
            ))}
          </div>

          {/* AI Summary */}
          {article.summary_ai && (
            <div className="bg-brand/5 border border-brand/20 rounded-xl p-5 mb-6">
              <p className="text-xs font-bold text-brand uppercase tracking-wider mb-2">AI Summary</p>
              <p className="text-slate-700 leading-relaxed">{article.summary_ai}</p>
            </div>
          )}

          {/* Relevance score */}
          <div className="flex items-center gap-3 mb-8">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Relevance</span>
            <div className="flex-1 max-w-32 bg-slate-100 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-brand"
                style={{ width: `${article.relevance_score * 100}%` }}
              />
            </div>
            <span className="text-sm font-bold text-slate-700">{Math.round(article.relevance_score * 100)}%</span>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-navy hover:bg-navy-light text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-colors"
            >
              Read full article <ExternalLink className="w-4 h-4" />
            </a>
            <Link
              href={`/admin/verify/${article.id}`}
              className="inline-flex items-center gap-2 border border-violet-200 text-violet-700 hover:bg-violet-50 font-semibold px-5 py-2.5 rounded-xl text-sm transition-colors"
            >
              <Shield className="w-4 h-4" /> Verify with AI
            </Link>
          </div>
        </div>
      </article>

      {/* Related by topic */}
      {article.topics.length > 0 && (
        <div className="mt-10">
          <h2 className="text-lg font-bold text-slate-900 mb-4">
            More in {TOPIC_LABELS[article.topics[0]] || article.topics[0]}
          </h2>
          <Link
            href={`/topics/${article.topics[0]}`}
            className="inline-flex items-center gap-2 text-sm text-brand font-semibold hover:underline"
          >
            Browse all {TOPIC_LABELS[article.topics[0]] || article.topics[0]} →
          </Link>
        </div>
      )}
    </div>
  );
}
