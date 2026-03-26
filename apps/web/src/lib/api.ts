const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Article {
  id: number;
  title: string;
  slug: string;
  url: string;
  summary_ai: string | null;
  image_url: string | null;
  author: string | null;
  topics: string[];
  regions: string[];
  reader_profiles: string[];
  sentiment: string | null;
  relevance_score: number;
  is_featured: boolean;
  published_at: string | null;
  scraped_at: string;
  source: {
    id: number;
    name: string;
    slug: string;
    logo_url: string | null;
    region: string;
  };
}

export interface ArticleList {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface Source {
  id: number;
  name: string;
  slug: string;
  url: string;
  rss_url: string | null;
  source_type: string;
  region: string;
  language: string;
  category: string;
  quality_score: number;
  is_active: boolean;
  description: string | null;
  logo_url: string | null;
}

export interface Topic {
  slug: string;
  label: string;
}

export interface Region {
  slug: string;
  label: string;
}

async function apiFetch<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_URL}/api${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    });
  }
  const res = await fetch(url.toString(), {
    next: { revalidate: 300 }, // 5 min ISR
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  articles: {
    list: (params?: Record<string, string>) =>
      apiFetch<ArticleList>("/articles", params),
    get: (slug: string) => apiFetch<Article>(`/articles/${slug}`),
    topics: () => apiFetch<Topic[]>("/articles/topics"),
    regions: () => apiFetch<Region[]>("/articles/regions"),
  },
  sources: {
    list: () => apiFetch<Source[]>("/sources"),
    get: (slug: string) => apiFetch<Source>(`/sources/${slug}`),
  },
  search: {
    query: (q: string, page = 1) =>
      apiFetch<ArticleList>("/search", { q, page: String(page) }),
  },
  subscriptions: {
    subscribe: async (data: {
      email: string;
      name?: string;
      reader_profile: string;
      topics: string[];
      regions: string[];
      frequency: string;
    }) => {
      const res = await fetch(`${API_URL}/api/subscriptions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Subscription failed");
      return res.json();
    },
  },
};
