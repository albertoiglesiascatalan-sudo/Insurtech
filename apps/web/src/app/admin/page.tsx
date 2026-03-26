import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth-options";
import { Newspaper, Globe, Users, Mail, TrendingUp, RefreshCw, Send, AlertCircle } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getStats(token: string) {
  try {
    const res = await fetch(`${API_URL}/api/admin/stats`, {
      headers: { Authorization: `Bearer ${token}` },
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function getRecentArticles(token: string) {
  try {
    const res = await fetch(`${API_URL}/api/articles?page_size=8`, {
      next: { revalidate: 120 },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.items || [];
  } catch {
    return [];
  }
}

export default async function AdminDashboard() {
  const session = await getServerSession(authOptions);
  const token = (session as any)?.accessToken || "";

  const [stats, recentArticles] = await Promise.all([
    getStats(token),
    getRecentArticles(token),
  ]);

  const statCards = [
    {
      label: "Total Articles",
      value: stats?.articles_total ?? "—",
      icon: Newspaper,
      color: "text-blue-600 bg-blue-50",
      sub: `${stats?.articles_duplicates ?? 0} duplicates filtered`,
    },
    {
      label: "Active Sources",
      value: stats?.sources_active ?? "—",
      icon: Globe,
      color: "text-emerald-600 bg-emerald-50",
      sub: "55+ global sources",
    },
    {
      label: "Total Users",
      value: stats?.users_total ?? "—",
      icon: Users,
      color: "text-violet-600 bg-violet-50",
      sub: "registered accounts",
    },
    {
      label: "Active Subscribers",
      value: stats?.subscribers_active ?? "—",
      icon: Mail,
      color: "text-amber-600 bg-amber-50",
      sub: "newsletter subscribers",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">InsurTech Intelligence — Admin Panel</p>
        </div>
        <div className="flex gap-3">
          <form action={`${API_URL}/api/admin/ingest`} method="POST">
            <button
              type="button"
              onClick={async () => {
                await fetch(`${API_URL}/api/admin/ingest`, {
                  method: "POST",
                  headers: { Authorization: `Bearer ${token}` },
                });
                window.location.reload();
              }}
              className="flex items-center gap-2 bg-white border border-slate-200 hover:border-brand text-slate-700 hover:text-brand font-semibold px-4 py-2 rounded-xl transition-colors text-sm"
            >
              <RefreshCw className="w-4 h-4" /> Run Ingestion
            </button>
          </form>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className="bg-white rounded-2xl border border-slate-200 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-500 mb-1">{card.label}</p>
                <p className="text-3xl font-bold text-slate-900">{card.value}</p>
                <p className="text-xs text-slate-400 mt-1">{card.sub}</p>
              </div>
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${card.color}`}>
                <card.icon className="w-5 h-5" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickAction
          href="/admin/sources"
          icon={Globe}
          title="Manage Sources"
          desc="Enable/disable sources, add new ones, check last fetch status"
          color="bg-emerald-50 border-emerald-200 hover:border-emerald-400"
          iconColor="text-emerald-600"
        />
        <QuickAction
          href="/admin/articles"
          icon={Newspaper}
          title="Moderate Articles"
          desc="Review incoming articles, feature top stories, remove off-topic content"
          color="bg-blue-50 border-blue-200 hover:border-blue-400"
          iconColor="text-blue-600"
        />
        <QuickAction
          href="/admin/newsletter"
          icon={Mail}
          title="Send Newsletter"
          desc="Generate and dispatch AI-written digests to subscribers"
          color="bg-amber-50 border-amber-200 hover:border-amber-400"
          iconColor="text-amber-600"
        />
      </div>

      {/* Recent articles */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900">Recent Ingested Articles</h2>
          <a href="/admin/articles" className="text-sm text-brand font-semibold hover:underline">View all →</a>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 divide-y divide-slate-100">
          {recentArticles.length === 0 ? (
            <div className="p-8 text-center text-slate-400">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-sm">No articles yet. Run ingestion to start.</p>
            </div>
          ) : (
            recentArticles.map((article: any) => (
              <div key={article.id} className="flex items-start gap-4 p-4 hover:bg-slate-50 transition-colors">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-800 line-clamp-1">{article.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-500">{article.source.name}</span>
                    {article.topics.slice(0, 2).map((t: string) => (
                      <span key={t} className="text-xs bg-brand/10 text-brand px-1.5 py-0.5 rounded">{t}</span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {article.is_featured && (
                    <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">Featured</span>
                  )}
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    article.sentiment === "positive" ? "bg-green-100 text-green-700" :
                    article.sentiment === "negative" ? "bg-red-100 text-red-700" :
                    "bg-slate-100 text-slate-600"
                  }`}>
                    {article.sentiment || "neutral"}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function QuickAction({ href, icon: Icon, title, desc, color, iconColor }: any) {
  return (
    <a href={href} className={`block rounded-2xl border-2 p-5 transition-all ${color}`}>
      <div className={`w-10 h-10 rounded-xl bg-white flex items-center justify-center mb-3 shadow-sm`}>
        <Icon className={`w-5 h-5 ${iconColor}`} />
      </div>
      <h3 className="font-bold text-slate-800 mb-1">{title}</h3>
      <p className="text-sm text-slate-500">{desc}</p>
    </a>
  );
}
