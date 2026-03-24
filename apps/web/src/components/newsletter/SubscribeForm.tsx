"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { TOPIC_LABELS } from "@/lib/utils";
import { CheckCircle, Loader2 } from "lucide-react";

const PROFILES = [
  { value: "investor", label: "Investor", emoji: "📈", desc: "Funding, M&A, market data" },
  { value: "founder", label: "Founder", emoji: "🚀", desc: "Products, tech, go-to-market" },
  { value: "general", label: "General", emoji: "🌐", desc: "Trends, innovation overview" },
];

export function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [profile, setProfile] = useState("general");
  const [topics, setTopics] = useState<string[]>([]);
  const [frequency, setFrequency] = useState("weekly");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const toggleTopic = (slug: string) => {
    setTopics((prev) =>
      prev.includes(slug) ? prev.filter((t) => t !== slug) : [...prev, slug]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.subscriptions.subscribe({ email, name, reader_profile: profile, topics, regions: [], frequency });
      setSuccess(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="text-center py-12">
        <CheckCircle className="w-16 h-16 text-brand mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-slate-900 mb-2">You're subscribed!</h2>
        <p className="text-slate-600">
          Welcome to InsurTech Intelligence. Your first newsletter is on its way.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl">
      {/* Email */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-1.5">Email address *</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com"
          className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand"
        />
      </div>

      {/* Name */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-1.5">Name (optional)</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Your name"
          className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand/50 focus:border-brand"
        />
      </div>

      {/* Reader profile */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">I am a...</label>
        <div className="grid grid-cols-3 gap-3">
          {PROFILES.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => setProfile(p.value)}
              className={`p-3 rounded-xl border-2 text-left transition-all ${
                profile === p.value
                  ? "border-brand bg-brand/5"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="text-xl mb-1">{p.emoji}</div>
              <div className="text-sm font-semibold text-slate-800">{p.label}</div>
              <div className="text-xs text-slate-500 mt-0.5">{p.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Topics */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">
          Topics of interest (optional)
        </label>
        <div className="flex flex-wrap gap-2">
          {Object.entries(TOPIC_LABELS).map(([slug, label]) => (
            <button
              key={slug}
              type="button"
              onClick={() => toggleTopic(slug)}
              className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                topics.includes(slug)
                  ? "bg-brand text-white border-brand"
                  : "border-slate-200 text-slate-600 hover:border-brand"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Frequency */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 mb-2">Frequency</label>
        <div className="flex gap-3">
          {["daily", "weekly"].map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFrequency(f)}
              className={`px-6 py-2.5 rounded-xl border-2 text-sm font-semibold capitalize transition-all ${
                frequency === f
                  ? "border-brand bg-brand text-white"
                  : "border-slate-200 text-slate-600 hover:border-slate-300"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-brand hover:bg-brand-dark disabled:opacity-60 text-white font-bold py-3.5 rounded-xl transition-colors flex items-center justify-center gap-2"
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
        {loading ? "Subscribing..." : "Subscribe for free →"}
      </button>

      <p className="text-xs text-slate-400 text-center">
        Free forever. No spam. Unsubscribe anytime with one click.
      </p>
    </form>
  );
}
