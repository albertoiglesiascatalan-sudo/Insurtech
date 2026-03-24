"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { TOPIC_LABELS, REGION_LABELS } from "@/lib/utils";
import { X } from "lucide-react";

const PROFILES = [
  { value: "investor", label: "Investors" },
  { value: "founder", label: "Founders" },
  { value: "general", label: "General" },
];

const SENTIMENTS = [
  { value: "positive", label: "Positive" },
  { value: "neutral", label: "Neutral" },
  { value: "negative", label: "Negative" },
];

export function ArticleFilters() {
  const router = useRouter();
  const params = useSearchParams();

  const updateFilter = useCallback(
    (key: string, value: string | null) => {
      const p = new URLSearchParams(params.toString());
      if (value) {
        p.set(key, value);
      } else {
        p.delete(key);
      }
      p.delete("page");
      router.push(`?${p.toString()}`);
    },
    [params, router]
  );

  const clearAll = () => router.push("?");

  const active = {
    topic: params.get("topic"),
    region: params.get("region"),
    profile: params.get("profile"),
    sentiment: params.get("sentiment"),
  };

  const hasFilters = Object.values(active).some(Boolean);

  return (
    <div className="space-y-4">
      {/* Topics */}
      <div>
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Topics</h3>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(TOPIC_LABELS).map(([slug, label]) => (
            <button
              key={slug}
              onClick={() => updateFilter("topic", active.topic === slug ? null : slug)}
              className={`text-xs px-2.5 py-1 rounded-full border font-medium transition-colors ${
                active.topic === slug
                  ? "bg-brand text-white border-brand"
                  : "border-slate-200 text-slate-600 hover:border-brand hover:text-brand bg-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Regions */}
      <div>
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Region</h3>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(REGION_LABELS).map(([slug, label]) => (
            <button
              key={slug}
              onClick={() => updateFilter("region", active.region === slug ? null : slug)}
              className={`text-xs px-2.5 py-1 rounded-full border font-medium transition-colors ${
                active.region === slug
                  ? "bg-navy text-white border-navy"
                  : "border-slate-200 text-slate-600 hover:border-navy hover:text-navy bg-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Reader profile */}
      <div>
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Reader Profile</h3>
        <div className="flex gap-1.5">
          {PROFILES.map((p) => (
            <button
              key={p.value}
              onClick={() => updateFilter("profile", active.profile === p.value ? null : p.value)}
              className={`text-xs px-2.5 py-1 rounded-full border font-medium transition-colors ${
                active.profile === p.value
                  ? "bg-amber-500 text-white border-amber-500"
                  : "border-slate-200 text-slate-600 hover:border-amber-400 bg-white"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Clear */}
      {hasFilters && (
        <button
          onClick={clearAll}
          className="flex items-center gap-1.5 text-xs text-red-500 hover:text-red-600 font-medium"
        >
          <X className="w-3.5 h-3.5" /> Clear filters
        </button>
      )}
    </div>
  );
}
