"use client";

import { useState, useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search, Loader2 } from "lucide-react";
import { Article } from "@/lib/api";
import { ArticleCard } from "@/components/articles/ArticleCard";

export default function SearchPage() {
  const params = useSearchParams();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [query, setQuery] = useState(params.get("q") || "");
  const [results, setResults] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/search?q=${encodeURIComponent(query)}`
      );
      const data = await res.json();
      setResults(data.items || []);
      setTotal(data.total || 0);
      setSearched(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-slate-900 mb-8">Search InsurTech News</h1>

      <form onSubmit={handleSearch} className="flex gap-3 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search articles, companies, topics..."
            className="w-full pl-12 pr-4 py-3.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="bg-brand hover:bg-brand-dark disabled:opacity-60 text-white font-semibold px-6 py-3.5 rounded-xl transition-colors flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          Search
        </button>
      </form>

      {searched && (
        <p className="text-sm text-slate-500 mb-6">
          {total} results for "<span className="font-semibold text-slate-700">{query}</span>"
        </p>
      )}

      {results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {results.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}

      {searched && results.length === 0 && (
        <div className="text-center py-16 text-slate-400">
          <Search className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="font-semibold mb-1">No results found</p>
          <p className="text-sm">Try different keywords or browse by topic</p>
        </div>
      )}

      {!searched && (
        <div className="text-center py-16 text-slate-400">
          <Search className="w-16 h-16 mx-auto mb-4 opacity-20" />
          <p className="text-lg font-medium mb-2">Search 55+ sources</p>
          <p className="text-sm">Find articles by company name, technology, person or event</p>
        </div>
      )}
    </div>
  );
}
