"use client";

import Link from "next/link";
import { useState } from "react";
import { Search, Menu, X, Zap, Wheat } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/news", label: "All News" },
  { href: "/topics", label: "Topics" },
  { href: "/for/investor", label: "Investors" },
  { href: "/for/founder", label: "Founders" },
  { href: "/newsletter", label: "Newsletter" },
  { href: "/bookmarks", label: "Saved" },
  { href: "/bakery", label: "🍞 Panadería" },
];

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-navy">
            <div className="w-8 h-8 rounded-lg bg-navy flex items-center justify-center">
              <Zap className="w-4 h-4 text-brand" />
            </div>
            <span className="text-lg font-bold text-slate-900">
              InsurTech<span className="text-brand">Intelligence</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <Link
              href="/search"
              className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
            >
              <Search className="w-5 h-5" />
            </Link>
            <Link
              href="/bakery"
              className="hidden md:flex items-center gap-1.5 p-2 text-amber-600 hover:text-amber-700 hover:bg-amber-50 rounded-lg transition"
              title="Panadería"
            >
              <Wheat className="w-5 h-5" />
            </Link>
            <Link
              href="/newsletter"
              className="hidden md:inline-flex items-center gap-1.5 bg-brand hover:bg-brand-dark text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Subscribe free
            </Link>
            <button
              className="md:hidden p-2 text-slate-500 hover:bg-slate-100 rounded-lg"
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden py-4 border-t border-slate-100 space-y-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 rounded-lg"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-2">
              <Link
                href="/newsletter"
                className="block w-full text-center bg-brand text-white text-sm font-semibold px-4 py-2 rounded-lg"
                onClick={() => setMobileOpen(false)}
              >
                Subscribe free →
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
