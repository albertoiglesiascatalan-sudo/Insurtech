"use client";

import Link from "next/link";
import Image from "next/image";
import { ExternalLink, Clock, TrendingUp, TrendingDown, Minus, Bookmark, BookmarkCheck } from "lucide-react";
import { useState, useEffect } from "react";
import { Article } from "@/lib/api";
import { cn, timeAgo, TOPIC_LABELS, REGION_LABELS, SENTIMENT_COLORS } from "@/lib/utils";
import { saveBookmark, removeBookmark, isBookmarked } from "@/app/bookmarks/page";

interface ArticleCardProps {
  article: Article;
  compact?: boolean;
}

const SENTIMENT_ICONS = {
  positive: TrendingUp,
  neutral: Minus,
  negative: TrendingDown,
};

export function ArticleCard({ article, compact = false }: ArticleCardProps) {
  const [bookmarked, setBookmarked] = useState(false);

  useEffect(() => {
    setBookmarked(isBookmarked(article.id));
  }, [article.id]);

  const toggleBookmark = (e: React.MouseEvent) => {
    e.preventDefault();
    if (bookmarked) {
      removeBookmark(article.id);
    } else {
      saveBookmark(article);
    }
    setBookmarked(!bookmarked);
  };

  const SentimentIcon = article.sentiment
    ? SENTIMENT_ICONS[article.sentiment as keyof typeof SENTIMENT_ICONS] || Minus
    : null;

  return (
    <article
      className={cn(
        "bg-white rounded-xl border border-slate-200 hover:border-brand/50 hover:shadow-md transition-all duration-200 overflow-hidden group",
        article.is_featured && "ring-2 ring-brand/30",
        compact && "flex gap-4"
      )}
    >
      {/* Image */}
      {!compact && article.image_url && (
        <div className="relative h-48 bg-slate-100 overflow-hidden">
          <Image
            src={article.image_url}
            alt={article.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            unoptimized
          />
          {article.is_featured && (
            <span className="absolute top-3 left-3 bg-brand text-white text-xs font-bold px-2 py-1 rounded">
              FEATURED
            </span>
          )}
        </div>
      )}

      <div className={cn("p-4 flex flex-col gap-3", compact && "flex-1 min-w-0")}>
        {/* Source + meta */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-xs font-semibold text-slate-500 truncate">
              {article.source.name}
            </span>
            {article.source.region !== "global" && (
              <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                {article.source.region}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {SentimentIcon && article.sentiment && (
              <SentimentIcon
                className={cn("w-3.5 h-3.5", SENTIMENT_COLORS[article.sentiment])}
              />
            )}
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {timeAgo(article.published_at || article.scraped_at)}
            </span>
          </div>
        </div>

        {/* Title */}
        <h2 className={cn("font-semibold text-slate-900 leading-snug group-hover:text-brand transition-colors", compact ? "text-sm line-clamp-2" : "text-base line-clamp-3")}>
          <Link href={`/news/${article.slug}`}>
            {article.title}
          </Link>
        </h2>

        {/* AI Summary */}
        {!compact && article.summary_ai && (
          <p className="text-sm text-slate-600 leading-relaxed line-clamp-3">
            {article.summary_ai}
          </p>
        )}

        {/* Topics */}
        {article.topics.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {article.topics.slice(0, compact ? 1 : 3).map((topic) => (
              <Link
                key={topic}
                href={`/topics/${topic}`}
                className="text-xs font-medium text-brand bg-brand/10 px-2 py-0.5 rounded-full hover:bg-brand hover:text-white transition-colors"
              >
                {TOPIC_LABELS[topic] || topic}
              </Link>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-1 mt-auto">
          <div className="flex gap-1">
            {article.regions.slice(0, 2).map((r) => (
              <Link
                key={r}
                href={`/regions/${r}`}
                className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
              >
                {r}
              </Link>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleBookmark}
              className={cn("p-1 rounded transition-colors", bookmarked ? "text-amber-500" : "text-slate-300 hover:text-amber-400")}
              title={bookmarked ? "Remove bookmark" : "Save article"}
            >
              {bookmarked ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
            </button>
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-slate-400 hover:text-brand flex items-center gap-1 transition-colors"
            >
              Read <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </article>
  );
}
