import Link from "next/link";
import { Zap } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-navy text-slate-300 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-brand/20 flex items-center justify-center">
                <Zap className="w-4 h-4 text-brand" />
              </div>
              <span className="text-white font-bold text-lg">
                InsurTech<span className="text-brand">Intelligence</span>
              </span>
            </Link>
            <p className="text-sm text-slate-400 max-w-xs">
              Global insurtech news from 55+ verified sources. AI-powered summaries,
              personalised by reader profile. Free newsletter.
            </p>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-3 text-sm">Browse</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/news" className="hover:text-brand transition-colors">All News</Link></li>
              <li><Link href="/topics" className="hover:text-brand transition-colors">Topics</Link></li>
              <li><Link href="/for/investor" className="hover:text-brand transition-colors">Investors</Link></li>
              <li><Link href="/for/founder" className="hover:text-brand transition-colors">Founders</Link></li>
              <li><Link href="/for/general" className="hover:text-brand transition-colors">General</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-3 text-sm">Regions</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/regions/US" className="hover:text-brand transition-colors">United States</Link></li>
              <li><Link href="/regions/EU" className="hover:text-brand transition-colors">Europe</Link></li>
              <li><Link href="/regions/APAC" className="hover:text-brand transition-colors">Asia Pacific</Link></li>
              <li><Link href="/regions/LATAM" className="hover:text-brand transition-colors">Latin America</Link></li>
              <li><Link href="/regions/MEA" className="hover:text-brand transition-colors">Middle East & Africa</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-700 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} InsurTech Intelligence. AI-curated global insurtech news.
          </p>
          <div className="flex gap-6 text-xs text-slate-500">
            <Link href="/newsletter/archive" className="hover:text-slate-300">Newsletter Archive</Link>
            <Link href="/sources" className="hover:text-slate-300">Sources</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
