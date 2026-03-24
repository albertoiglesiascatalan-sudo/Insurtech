"use client";

import { useState } from "react";
import { Star, EyeOff, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ArticleActions({ articleId, isFeatured }: { articleId: number; isFeatured: boolean }) {
  const [featured, setFeatured] = useState(isFeatured);
  const [loadingFeature, setLoadingFeature] = useState(false);
  const [loadingUnpublish, setLoadingUnpublish] = useState(false);
  const [unpublished, setUnpublished] = useState(false);
  const router = useRouter();

  const toggleFeature = async () => {
    setLoadingFeature(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/articles/${articleId}/feature`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setFeatured(data.is_featured);
        router.refresh();
      }
    } finally {
      setLoadingFeature(false);
    }
  };

  const unpublish = async () => {
    if (!confirm("Unpublish this article? It will be hidden from the feed.")) return;
    setLoadingUnpublish(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/articles/${articleId}/unpublish`, { method: "POST" });
      if (res.ok) {
        setUnpublished(true);
        router.refresh();
      }
    } finally {
      setLoadingUnpublish(false);
    }
  };

  if (unpublished) return <span className="text-xs text-slate-400 italic">hidden</span>;

  return (
    <>
      <button
        onClick={toggleFeature}
        disabled={loadingFeature}
        title={featured ? "Unfeature" : "Feature"}
        className={`p-1.5 rounded-lg transition-colors disabled:opacity-50 ${
          featured
            ? "text-amber-500 bg-amber-50 hover:bg-amber-100"
            : "text-slate-400 hover:text-amber-500 hover:bg-amber-50"
        }`}
      >
        {loadingFeature ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Star className="w-3.5 h-3.5" />}
      </button>
      <button
        onClick={unpublish}
        disabled={loadingUnpublish}
        title="Unpublish"
        className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
      >
        {loadingUnpublish ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <EyeOff className="w-3.5 h-3.5" />}
      </button>
    </>
  );
}
