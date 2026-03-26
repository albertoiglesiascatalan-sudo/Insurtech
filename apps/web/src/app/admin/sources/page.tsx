import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth-options";
import { Globe, CheckCircle, XCircle, Clock, RefreshCw, Plus } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getSources() {
  try {
    const res = await fetch(`${API_URL}/api/sources?active_only=false`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

const CATEGORY_LABELS: Record<string, string> = {
  trade: "Trade Press",
  vc: "VC / Startup",
  regulatory: "Regulatory",
  research: "Research",
  fintech: "Fintech",
  press: "General Press",
  tech: "Tech / Cyber",
  general: "General",
};

const REGION_COLORS: Record<string, string> = {
  US: "bg-blue-100 text-blue-700",
  EU: "bg-indigo-100 text-indigo-700",
  APAC: "bg-emerald-100 text-emerald-700",
  LATAM: "bg-orange-100 text-orange-700",
  MEA: "bg-purple-100 text-purple-700",
  global: "bg-slate-100 text-slate-600",
};

export default async function AdminSourcesPage() {
  const sources = await getSources();

  const byRegion = sources.reduce((acc: any, s: any) => {
    if (!acc[s.region]) acc[s.region] = [];
    acc[s.region].push(s);
    return acc;
  }, {} as Record<string, any[]>);

  const active = sources.filter((s: any) => s.is_active).length;
  const inactive = sources.filter((s: any) => !s.is_active).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">News Sources</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {sources.length} total · {active} active · {inactive} inactive
          </p>
        </div>
        <button className="flex items-center gap-2 bg-brand hover:bg-brand-dark text-white font-semibold px-4 py-2 rounded-xl transition-colors text-sm">
          <Plus className="w-4 h-4" /> Add Source
        </button>
      </div>

      {/* Summary by region */}
      <div className="grid grid-cols-3 lg:grid-cols-6 gap-3">
        {Object.entries(byRegion).map(([region, srcs]: [string, any]) => (
          <div key={region} className="bg-white rounded-xl border border-slate-200 p-3 text-center">
            <p className="text-2xl font-bold text-slate-900">{(srcs as any[]).length}</p>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${REGION_COLORS[region] || "bg-slate-100 text-slate-600"}`}>
              {region}
            </span>
          </div>
        ))}
      </div>

      {/* Sources table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Source</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Region</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Category</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Type</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Quality</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Last Fetch</th>
                <th className="text-left px-4 py-3 font-semibold text-slate-600">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sources.map((source: any) => (
                <tr key={source.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-800">{source.name}</div>
                    <a href={source.url} target="_blank" rel="noopener noreferrer"
                       className="text-xs text-slate-400 hover:text-brand truncate block max-w-[200px]">
                      {source.url}
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${REGION_COLORS[source.region] || "bg-slate-100 text-slate-600"}`}>
                      {source.region}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 text-xs">
                    {CATEGORY_LABELS[source.category] || source.category}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                      source.source_type === "rss"
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-orange-100 text-orange-700"
                    }`}>
                      {source.source_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-100 rounded-full h-1.5 w-16">
                        <div
                          className="h-1.5 rounded-full bg-brand"
                          style={{ width: `${source.quality_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-500">{Math.round(source.quality_score * 100)}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {source.last_fetched_at
                      ? formatDistanceToNow(new Date(source.last_fetched_at), { addSuffix: true })
                      : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    {source.is_active ? (
                      <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium">
                        <CheckCircle className="w-3.5 h-3.5" /> Active
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-red-500 font-medium">
                        <XCircle className="w-3.5 h-3.5" /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <ToggleSourceButton source={source} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ToggleSourceButton({ source }: { source: any }) {
  return (
    <button
      className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors border ${
        source.is_active
          ? "border-red-200 text-red-600 hover:bg-red-50"
          : "border-emerald-200 text-emerald-600 hover:bg-emerald-50"
      }`}
    >
      {source.is_active ? "Disable" : "Enable"}
    </button>
  );
}
