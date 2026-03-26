"use client";

import { useState } from "react";
import { Mail, Send, Loader2, CheckCircle, Users } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PROFILES = [
  { value: "investor", label: "Investor Edition", emoji: "📈", desc: "Funding, M&A, market intelligence" },
  { value: "founder", label: "Founder Edition", emoji: "🚀", desc: "Products, tech, partnerships" },
  { value: "general", label: "General Edition", emoji: "🌐", desc: "Macro trends, innovation overview" },
];

const FREQUENCIES = [
  { value: "daily", label: "Daily Digest" },
  { value: "weekly", label: "Weekly Digest" },
];

export default function AdminNewsletterPage() {
  const [profile, setProfile] = useState("general");
  const [frequency, setFrequency] = useState("weekly");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleSend = async () => {
    setSending(true);
    setResult(null);
    try {
      const res = await fetch(
        `${API_URL}/api/admin/newsletter/send?profile=${profile}&frequency=${frequency}`,
        { method: "POST" }
      );
      if (res.ok) {
        setResult({ success: true, message: `Newsletter ${frequency}/${profile} queued for sending!` });
      } else {
        setResult({ success: false, message: "Failed to queue newsletter. Check API logs." });
      }
    } catch {
      setResult({ success: false, message: "Network error. Is the API running?" });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Send Newsletter</h1>
        <p className="text-slate-500 text-sm mt-0.5">Generate and dispatch AI-written digests to subscribers</p>
      </div>

      {/* Profile selector */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
        <h2 className="font-semibold text-slate-800">1. Reader Profile</h2>
        <div className="grid grid-cols-3 gap-3">
          {PROFILES.map((p) => (
            <button
              key={p.value}
              onClick={() => setProfile(p.value)}
              className={`p-4 rounded-xl border-2 text-left transition-all ${
                profile === p.value
                  ? "border-brand bg-brand/5"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="text-2xl mb-2">{p.emoji}</div>
              <div className="text-sm font-bold text-slate-800">{p.label}</div>
              <div className="text-xs text-slate-500 mt-0.5">{p.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Frequency selector */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
        <h2 className="font-semibold text-slate-800">2. Frequency</h2>
        <div className="flex gap-3">
          {FREQUENCIES.map((f) => (
            <button
              key={f.value}
              onClick={() => setFrequency(f.value)}
              className={`px-6 py-3 rounded-xl border-2 font-semibold transition-all text-sm ${
                frequency === f.value
                  ? "border-brand bg-brand text-white"
                  : "border-slate-200 text-slate-600 hover:border-slate-300"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Preview info */}
      <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-brand/10 rounded-xl flex items-center justify-center shrink-0">
            <Mail className="w-5 h-5 text-brand" />
          </div>
          <div>
            <p className="font-semibold text-slate-800 text-sm">What will be sent</p>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              GPT-4o will select the top articles from the last {frequency === "daily" ? "24 hours" : "7 days"} for
              the <strong>{profile}</strong> profile, write an editorial narrative with sections grouped by topic,
              and send it to all active <strong>{frequency}</strong> subscribers with profile <strong>{profile}</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className={`flex items-center gap-3 p-4 rounded-xl border ${
          result.success
            ? "bg-green-50 border-green-200 text-green-700"
            : "bg-red-50 border-red-200 text-red-600"
        }`}>
          <CheckCircle className="w-5 h-5 shrink-0" />
          <p className="text-sm font-medium">{result.message}</p>
        </div>
      )}

      {/* Send button */}
      <button
        onClick={handleSend}
        disabled={sending}
        className="w-full bg-navy hover:bg-navy-light disabled:opacity-60 text-white font-bold py-4 rounded-xl transition-colors flex items-center justify-center gap-2 text-base"
      >
        {sending ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating &amp; sending...
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            Generate &amp; Send Newsletter
          </>
        )}
      </button>
    </div>
  );
}
