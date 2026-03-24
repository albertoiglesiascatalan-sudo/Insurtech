"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Bookmark, Trash2, ExternalLink } from "lucide-react";
import { TOPIC_LABELS, timeAgo } from "@/lib/utils";

interface BookmarkedArticle {
  id: number;
  title: string;
  slug: string;
  url: string;
  summary_ai: string | null;
  topics: string[];
  source: { name: string };
  published_at: string | null;
  scraped_at: string;
  savedAt: string;
}

const STORAGE_KEY = "insurtech_bookmarks";

export function getBookmarks(): BookmarkedArticle[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

export function saveBookmark(article: Omit<BookmarkedArticle, "savedAt">) {
  const bookmarks = getBookmarks();
  if (bookmarks.find((b) => b.id === article.id)) return;
  bookmarks.unshift({ ...article, savedAt: new Date().toISOString() });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
}

export function removeBookmark(id: number) {
  const bookmarks = getBookmarks().filter((b) => b.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
}

export function isBookmarked(id: number): boolean {
  return getBookmarks().some((b) => b.id === id);
}

export default function BookmarksPage() {
  const [bookmarks, setBookmarks] = useState<BookmarkedArticle[]>([]);

  useEffect(() => {
    setBookmarks(getBookmarks());
  }, []);

  const remove = (id: number) => {
    removeBookmark(id);
    setBookmarks(getBookmarks());
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center">
          <Bookmark className="w-5 h-5 text-amber-500" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Saved articles</h1>
          <p className="text-slate-500 text-sm">{bookmarks.length} {bookmarks.length === 1 ? "article" : "articles"} saved</p>
        </div>
      </div>

      {bookmarks.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <Bookmark className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-medium mb-1">No saved articles yet</p>
          <p className="text-sm text-slate-400 mb-6">Bookmark articles while browsing and they'll appear here</p>
          <Link
            href="/news"
            className="inline-flex items-center gap-2 bg-brand text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-brand-dark transition-colors"
          >
            Browse news →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {bookmarks.map((article) => (
            <div
              key={article.id}
              className="bg-white rounded-xl border border-slate-200 p-5 hover:border-brand/40 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/news/${article.slug}`}
                    className="font-semibold text-slate-900 hover:text-brand transition-colors line-clamp-2 block"
                  >
                    {article.title}
                  </Link>
                  {article.summary_ai && (
                    <p className="text-sm text-slate-500 mt-1.5 line-clamp-2">{article.summary_ai}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-2 mt-3">
                    <span className="text-xs font-semibold text-slate-500">{article.source.name}</span>
                    <span className="text-slate-300">·</span>
                    <span className="text-xs text-slate-400">saved {timeAgo(article.savedAt)}</span>
                    {article.topics.slice(0, 2).map((t) => (
                      <span key={t} className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded-full">
                        {TOPIC_LABELS[t] || t}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 text-slate-400 hover:text-brand hover:bg-slate-50 rounded-lg transition-colors"
                    title="Open original"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                  <button
                    onClick={() => remove(article.id)}
                    className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="Remove bookmark"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
