import { Suspense } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { ArticleCard } from "@/components/articles/ArticleCard";
import { ArticleFilters } from "@/components/articles/ArticleFilters";
import { TOPIC_LABELS, REGION_LABELS } from "@/lib/utils";

interface PageProps {
  searchParams: Promise<Record<string, string>>;
}

export const metadata = {
  title: "All News",
  description: "Browse all insurtech news from 55+ global verified sources. Filter by topic, region and reader profile.",
};

async function NewsFeed({ searchParams }: { searchParams: Record<string, string> }) {
  const page = parseInt(searchParams.page || "1");
  const data = await api.articles.list({
    topic: searchParams.topic,
    region: searchParams.region,
    profile: searchParams.profile,
    sentiment: searchParams.sentiment,
    search: searchParams.search,
    featured_only: searchParams.featured_only,
    page: String(page),
    page_size: "20",
  }).catch(() => ({ items: [], total: 0, page, page_size: 20, has_next: false }));

  const title = [
    searchParams.topic && TOPIC_LABELS[searchParams.topic],
    searchParams.region && REGION_LABELS[searchParams.region],
    searchParams.profile && `${searchParams.profile.charAt(0).toUpperCase() + searchParams.profile.slice(1)} edition`,
  ].filter(Boolean).join(" · ");

  return (
    <div>
      {title && (
        <div className="mb-6 p-4 bg-brand/5 border border-brand/20 rounded-xl">
          <p className="text-sm font-medium text-brand">Filtered: {title}</p>
          <p className="text-xs text-slate-500 mt-0.5">{data.total} articles found</p>
        </div>
      )}

      {data.items.length === 0 ? (
        <div className="text-center py-20 text-slate-400 bg-white rounded-2xl border">
          <p className="text-lg font-semibold mb-1">No articles found</p>
          <p className="text-sm">Try adjusting your filters</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {data.items.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-center gap-2 mt-10">
            {page > 1 && (
              <Link
                href={`?${new URLSearchParams({ ...searchParams, page: String(page - 1) })}`}
                className="px-5 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:border-brand transition-colors"
              >
                ← Previous
              </Link>
            )}
            <span className="px-5 py-2 text-sm text-slate-500">Page {page} · {data.total} total</span>
            {data.has_next && (
              <Link
                href={`?${new URLSearchParams({ ...searchParams, page: String(page + 1) })}`}
                className="px-5 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:border-brand transition-colors"
              >
                Next →
              </Link>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default async function NewsPage({ searchParams }: PageProps) {
  const sp = await searchParams;
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar filters */}
        <aside className="lg:w-64 shrink-0">
          <div className="sticky top-24 bg-white rounded-2xl border border-slate-200 p-5">
            <h2 className="font-bold text-slate-900 mb-4">Filter news</h2>
            <Suspense>
              <ArticleFilters />
            </Suspense>
          </div>
        </aside>

        {/* Main feed */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-slate-900">InsurTech News</h1>
            <Link href="/search" className="text-sm text-brand font-medium hover:underline">
              Search →
            </Link>
          </div>
          <Suspense fallback={<div className="animate-pulse space-y-4">{Array.from({length:6}).map((_,i)=><div key={i} className="h-48 bg-slate-200 rounded-xl"/>)}</div>}>
            <NewsFeed searchParams={sp} />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
