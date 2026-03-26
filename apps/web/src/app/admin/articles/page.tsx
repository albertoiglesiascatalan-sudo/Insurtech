import { ExternalLink, Shield } from "lucide-react";
import { timeAgo } from "@/lib/utils";
import Link from "next/link";
import { ArticleActions } from "./ArticleActions";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getArticles(page = 1) {
  try {
    const res = await fetch(`${API_URL}/api/articles?page=${page}&page_size=30`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return { items: [], total: 0 };
    return res.json();
  } catch {
    return { items: [], total: 0 };
  }
}

interface PageProps {
  searchParams: Promise<{ page?: string }>;
}

export default async function AdminArticlesPage({ searchParams }: PageProps) {
  const sp = await searchParams;
  const page = parseInt(sp.page || "1");
  const data = await getArticles(page);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Articles</h1>
          <p className="text-slate-500 text-sm mt-0.5">{data.total} total articles</p>
        </div>
        <div className="flex gap-2 text-sm">
          <span className="bg-slate-100 text-slate-600 px-3 py-1.5 rounded-lg font-medium">
            Page {page}
          </span>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Article</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Topics</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Sentiment</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Score</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Verify</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Published</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((article: any) => (
                <tr key={article.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 max-w-xs">
                    <p className="font-semibold text-slate-800 line-clamp-2 text-xs leading-relaxed">
                      {article.title}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">{article.source.name}</p>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {article.topics.slice(0, 2).map((t: string) => (
                        <span key={t} className="text-xs bg-brand/10 text-brand px-1.5 py-0.5 rounded">
                          {t.split("-").map((w: string) => w[0].toUpperCase() + w.slice(1)).join(" ")}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                      article.sentiment === "positive" ? "bg-green-100 text-green-700" :
                      article.sentiment === "negative" ? "bg-red-100 text-red-700" :
                      "bg-slate-100 text-slate-600"
                    }`}>
                      {article.sentiment || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <div className="w-12 bg-slate-100 rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full bg-brand"
                          style={{ width: `${article.relevance_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-500">{Math.round(article.relevance_score * 100)}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/admin/verify/${article.id}`}
                      className="flex items-center gap-1 text-xs text-violet-600 hover:text-violet-800 font-medium transition-colors"
                    >
                      <Shield className="w-3.5 h-3.5" /> Verify
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {timeAgo(article.published_at || article.scraped_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 text-slate-400 hover:text-brand rounded-lg hover:bg-slate-100 transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                      <ArticleActions articleId={article.id} isFeatured={article.is_featured} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex justify-center gap-2">
        {page > 1 && (
          <Link href={`?page=${page - 1}`} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm hover:border-brand">
            ← Previous
          </Link>
        )}
        {data.has_next && (
          <Link href={`?page=${page + 1}`} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm hover:border-brand">
            Next →
          </Link>
        )}
      </div>
    </div>
  );
}

