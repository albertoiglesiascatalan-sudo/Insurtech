import Link from "next/link";
import { api } from "@/lib/api";
import { ArticleCard } from "@/components/articles/ArticleCard";
import { SubscribeForm } from "@/components/newsletter/SubscribeForm";
import { Zap, Globe, Brain, TrendingUp, Rocket, Users } from "lucide-react";

const TOPIC_HIGHLIGHTS = [
  { slug: "funding-ma", label: "Funding & M&A", icon: TrendingUp },
  { slug: "ai-insurance", label: "AI in Insurance", icon: Brain },
  { slug: "embedded-insurance", label: "Embedded", icon: Zap },
  { slug: "regulatory-policy", label: "Regulatory", icon: Globe },
  { slug: "product-launches", label: "Product Launches", icon: Rocket },
];

const PROFILE_CARDS = [
  {
    href: "/for/investor",
    emoji: "📈",
    title: "For Investors",
    desc: "Funding rounds, M&A, valuations, market opportunities and competitive intelligence.",
    color: "bg-amber-50 border-amber-200 hover:border-amber-400",
  },
  {
    href: "/for/founder",
    emoji: "🚀",
    title: "For Founders",
    desc: "Product launches, partnerships, regulatory updates, and technology innovations.",
    color: "bg-blue-50 border-blue-200 hover:border-blue-400",
  },
  {
    href: "/for/general",
    emoji: "🌐",
    title: "General Edition",
    desc: "Macro trends, consumer innovation, and the biggest stories reshaping insurance.",
    color: "bg-emerald-50 border-emerald-200 hover:border-emerald-400",
  },
];

export default async function HomePage() {
  const [featuredData, latestData] = await Promise.all([
    api.articles.list({ featured_only: "true", page_size: "6" }).catch(() => ({ items: [] })),
    api.articles.list({ page_size: "12" }).catch(() => ({ items: [] })),
  ]);

  const featured = featuredData.items || [];
  const latest = latestData.items || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Hero */}
      <section className="py-16 text-center">
        <div className="inline-flex items-center gap-2 bg-brand/10 text-brand text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
          <Zap className="w-3.5 h-3.5" /> AI-powered · 55+ global sources · Free
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 leading-tight mb-6">
          The world's best<br />
          <span className="text-brand">InsurTech newsletter</span>
        </h1>
        <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-8">
          Global insurtech intelligence from 55+ verified sources. AI-summarised,
          deduplicated, and personalised for investors, founders, and professionals.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/newsletter"
            className="bg-brand hover:bg-brand-dark text-white font-bold px-8 py-3.5 rounded-xl transition-colors text-base"
          >
            Subscribe free →
          </Link>
          <Link
            href="/news"
            className="bg-white border-2 border-slate-200 hover:border-slate-300 text-slate-700 font-semibold px-8 py-3.5 rounded-xl transition-colors text-base"
          >
            Browse news
          </Link>
        </div>

        {/* Stats */}
        <div className="flex justify-center gap-12 mt-12 text-sm text-slate-500">
          <div><span className="text-2xl font-bold text-slate-900">55+</span><br />Global sources</div>
          <div><span className="text-2xl font-bold text-slate-900">15</span><br />Topic categories</div>
          <div><span className="text-2xl font-bold text-slate-900">3</span><br />Reader profiles</div>
          <div><span className="text-2xl font-bold text-slate-900">AI</span><br />Powered summaries</div>
        </div>
      </section>

      {/* Reader profiles */}
      <section className="mb-14">
        <h2 className="text-2xl font-bold text-slate-900 mb-6">Personalised for you</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {PROFILE_CARDS.map((p) => (
            <Link
              key={p.href}
              href={p.href}
              className={`rounded-2xl border-2 p-6 transition-all ${p.color}`}
            >
              <div className="text-3xl mb-3">{p.emoji}</div>
              <h3 className="font-bold text-slate-900 mb-1.5">{p.title}</h3>
              <p className="text-sm text-slate-600">{p.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Topic quick-links */}
      <section className="mb-14">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-slate-900">Browse by Topic</h2>
          <Link href="/topics" className="text-sm text-brand font-semibold hover:underline">All 15 topics →</Link>
        </div>
        <div className="flex flex-wrap gap-2">
          {TOPIC_HIGHLIGHTS.map(({ slug, label, icon: Icon }) => (
            <Link
              key={slug}
              href={`/topics/${slug}`}
              className="flex items-center gap-2 bg-white border border-slate-200 hover:border-brand hover:bg-brand/5 text-slate-700 hover:text-brand text-sm font-medium px-4 py-2 rounded-full transition-all"
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </div>
      </section>

      {/* Featured articles */}
      {featured.length > 0 && (
        <section className="mb-14">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Featured Stories</h2>
            <Link href="/news?featured_only=true" className="text-sm text-brand font-semibold hover:underline">View all →</Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featured.slice(0, 6).map((a) => (
              <ArticleCard key={a.id} article={a} />
            ))}
          </div>
        </section>
      )}

      {/* Latest news */}
      <section className="mb-14">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900">Latest News</h2>
          <Link href="/news" className="text-sm text-brand font-semibold hover:underline">View all →</Link>
        </div>
        {latest.length === 0 ? (
          <div className="text-center py-20 text-slate-400 bg-white rounded-2xl border border-slate-200">
            <p className="text-lg font-medium mb-2">No articles yet</p>
            <p className="text-sm">Run ingestion to populate with fresh insurtech news.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {latest.map((a) => (
              <ArticleCard key={a.id} article={a} />
            ))}
          </div>
        )}
      </section>

      {/* Subscribe CTA */}
      <section className="mb-16 bg-navy rounded-3xl p-10 text-center">
        <h2 className="text-3xl font-bold text-white mb-3">Never miss a story</h2>
        <p className="text-slate-300 mb-8 max-w-md mx-auto">
          Join thousands of insurtech professionals. Daily or weekly digest, personalised to your profile.
        </p>
        <div className="max-w-md mx-auto">
          <Link
            href="/newsletter"
            className="inline-block bg-brand hover:bg-brand-dark text-white font-bold px-10 py-3.5 rounded-xl transition-colors"
          >
            Get InsurTech Intelligence free →
          </Link>
        </div>
      </section>
    </div>
  );
}
