import { notFound } from "next/navigation";
import Link from "next/link";
import {
  Shield, ShieldCheck, ShieldAlert, ShieldX,
  CheckCircle, AlertCircle, XCircle, ExternalLink,
  ArrowLeft, TrendingUp, BookOpen, AlertTriangle
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getVerification(id: string) {
  try {
    const res = await fetch(`${API_URL}/api/verify/${id}`, {
      next: { revalidate: 3600 }, // cache 1h — expensive AI call
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

interface PageProps {
  params: Promise<{ id: string }>;
}

const VERDICT_CONFIG: Record<string, {
  icon: any; label: string; color: string; bg: string; border: string;
}> = {
  verified: {
    icon: ShieldCheck,
    label: "Verified",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
  },
  likely_true: {
    icon: ShieldCheck,
    label: "Likely True",
    color: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  unverified: {
    icon: Shield,
    label: "Unverified",
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  misleading: {
    icon: ShieldAlert,
    label: "Misleading",
    color: "text-orange-600",
    bg: "bg-orange-50",
    border: "border-orange-200",
  },
  false: {
    icon: ShieldX,
    label: "False",
    color: "text-red-600",
    bg: "bg-red-50",
    border: "border-red-200",
  },
};

const CLAIM_COLORS: Record<string, string> = {
  verified: "bg-emerald-100 text-emerald-700",
  plausible: "bg-blue-100 text-blue-700",
  unverified: "bg-amber-100 text-amber-700",
  questionable: "bg-red-100 text-red-700",
};

const RECOMMENDATION_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  trustworthy: { label: "Trustworthy source", color: "text-emerald-600", icon: CheckCircle },
  read_with_caution: { label: "Read with caution", color: "text-amber-600", icon: AlertCircle },
  verify_independently: { label: "Verify independently", color: "text-orange-600", icon: AlertTriangle },
  discard: { label: "Discard — unreliable", color: "text-red-600", icon: XCircle },
};

export default async function VerifyPage({ params }: PageProps) {
  const { id } = await params;
  const data = await getVerification(id);

  if (!data) {
    notFound();
  }

  const verdict = VERDICT_CONFIG[data.verdict] || VERDICT_CONFIG.unverified;
  const VerdictIcon = verdict.icon;
  const rec = RECOMMENDATION_CONFIG[data.recommendation] || RECOMMENDATION_CONFIG.read_with_caution;
  const RecIcon = rec.icon;

  return (
    <div className="space-y-6 max-w-4xl">
      <Link
        href="/admin/articles"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Articles
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Shield className="w-6 h-6 text-violet-600" />
          News Verifier
        </h1>
        <p className="text-slate-500 text-sm mt-0.5">AI-powered credibility analysis</p>
      </div>

      {/* Article info */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">Article</p>
        <h2 className="font-bold text-slate-900 text-lg leading-snug mb-2">{data.title}</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">{data.source_name}</span>
          <div className="flex items-center gap-1.5">
            <div className="w-16 bg-slate-100 rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full bg-brand"
                style={{ width: `${data.source_quality * 100}%` }}
              />
            </div>
            <span className="text-xs text-slate-500">Source quality: {Math.round(data.source_quality * 100)}%</span>
          </div>
        </div>
      </div>

      {/* Main verdict */}
      <div className={`rounded-2xl border-2 p-6 ${verdict.bg} ${verdict.border}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={`w-16 h-16 rounded-2xl bg-white flex items-center justify-center shadow-sm`}>
              <VerdictIcon className={`w-8 h-8 ${verdict.color}`} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500 mb-0.5">Credibility Verdict</p>
              <h3 className={`text-2xl font-bold ${verdict.color}`}>{verdict.label}</h3>
              <p className="text-sm text-slate-600 mt-0.5">{data.verdict_label}</p>
            </div>
          </div>

          {/* Score meter */}
          <div className="text-right">
            <p className="text-4xl font-bold text-slate-900">{Math.round(data.credibility_score * 100)}</p>
            <p className="text-sm text-slate-500">/ 100</p>
            <p className="text-xs text-slate-400 mt-1">AI confidence: {Math.round(data.confidence * 100)}%</p>
          </div>
        </div>

        {/* Summary */}
        <p className="mt-4 text-slate-700 leading-relaxed">{data.summary}</p>

        {/* Recommendation */}
        <div className="mt-4 flex items-center gap-2">
          <RecIcon className={`w-4 h-4 ${rec.color}`} />
          <span className={`text-sm font-semibold ${rec.color}`}>{rec.label}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Red flags */}
        {data.red_flags.length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Red Flags
            </h3>
            <ul className="space-y-2">
              {data.red_flags.map((flag: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm text-red-700">
                  <XCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Positive signals */}
        {data.positive_signals.length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-4">
              <CheckCircle className="w-4 h-4 text-emerald-500" />
              Positive Signals
            </h3>
            <ul className="space-y-2">
              {data.positive_signals.map((sig: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm text-emerald-700">
                  <CheckCircle className="w-4 h-4 shrink-0 mt-0.5 text-emerald-500" />
                  {sig}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Claim analysis */}
      {data.claim_analysis.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-4">
            <BookOpen className="w-4 h-4 text-violet-600" />
            Claim-by-Claim Analysis
          </h3>
          <div className="space-y-3">
            {data.claim_analysis.map((item: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
                <span className={`text-xs font-bold px-2 py-1 rounded-full shrink-0 mt-0.5 ${CLAIM_COLORS[item.assessment] || "bg-slate-100 text-slate-600"}`}>
                  {item.assessment.toUpperCase()}
                </span>
                <div>
                  <p className="text-sm font-medium text-slate-800">{item.claim}</p>
                  {item.note && <p className="text-xs text-slate-500 mt-0.5">{item.note}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Corroborating articles */}
      {data.corroborating_articles.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-emerald-500" />
            Corroborating Coverage
            <span className="text-xs font-normal text-slate-400">({data.corroborating_articles.length} similar articles)</span>
          </h3>
          <div className="space-y-2">
            {data.corroborating_articles.map((art: any) => (
              <div key={art.id} className="flex items-start justify-between gap-3 p-3 bg-emerald-50 rounded-xl">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800 line-clamp-1">{art.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-slate-500">{art.source}</span>
                    <span className="text-xs text-emerald-600 font-semibold">
                      {Math.round(art.similarity * 100)}% similar
                    </span>
                  </div>
                </div>
                <a href={art.url} target="_blank" rel="noopener noreferrer"
                   className="text-slate-400 hover:text-brand shrink-0 mt-0.5">
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contradicting articles */}
      {data.contradicting_articles.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-4">
            <AlertCircle className="w-4 h-4 text-orange-500" />
            Contradicting Coverage
            <span className="text-xs font-normal text-slate-400">(different sentiment)</span>
          </h3>
          <div className="space-y-2">
            {data.contradicting_articles.map((art: any) => (
              <div key={art.id} className="flex items-start justify-between gap-3 p-3 bg-orange-50 rounded-xl">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800 line-clamp-1">{art.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-slate-500">{art.source}</span>
                    <span className="text-xs text-orange-600 font-semibold">
                      {Math.round(art.similarity * 100)}% related
                    </span>
                  </div>
                </div>
                <a href={art.url} target="_blank" rel="noopener noreferrer"
                   className="text-slate-400 hover:text-brand shrink-0 mt-0.5">
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
