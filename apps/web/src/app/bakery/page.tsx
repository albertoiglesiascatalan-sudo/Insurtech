"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { ShoppingCart, Wheat, Search } from "lucide-react";
import { ProductCard } from "@/components/bakery/ProductCard";
import { useCart } from "@/components/bakery/CartContext";
import {
  BAKERY_PRODUCTS,
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  type BakeryCategory,
} from "@/lib/bakery-data";
import { cn } from "@/lib/utils";

const ALL = "all" as const;
type Filter = BakeryCategory | typeof ALL;

export default function BakeryPage() {
  const { totalItems, totalPrice } = useCart();
  const [activeCategory, setActiveCategory] = useState<Filter>(ALL);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    return BAKERY_PRODUCTS.filter((p) => {
      const matchCat = activeCategory === ALL || p.category === activeCategory;
      const q = search.toLowerCase();
      const matchSearch =
        q === "" ||
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some((t) => t.toLowerCase().includes(q));
      return matchCat && matchSearch;
    });
  }, [activeCategory, search]);

  const categories = Object.keys(CATEGORY_LABELS) as BakeryCategory[];

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Hero banner */}
      <div className="bg-gradient-to-br from-amber-600 via-orange-500 to-amber-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                  <Wheat className="w-5 h-5 text-white" />
                </div>
                <span className="text-amber-100 font-medium text-sm uppercase tracking-wider">
                  Obrador Artesanal
                </span>
              </div>
              <h1 className="text-4xl sm:text-5xl font-bold mb-3">
                La Tahona<span className="text-amber-200"> del Barrio</span>
              </h1>
              <p className="text-amber-100 text-lg max-w-xl">
                Pan artesanal horneado cada mañana. Sin aditivos, sin conservantes.
                Solo ingredientes de calidad y tiempo.
              </p>
              <div className="flex items-center gap-4 mt-5 text-sm text-amber-200">
                <span>🕕 Horneado diario a las 6:00</span>
                <span>•</span>
                <span>🚚 Envío gratis +30 €</span>
                <span>•</span>
                <span>♻️ Embalaje ecológico</span>
              </div>
            </div>

            {/* Cart summary */}
            <Link
              href="/bakery/cart"
              className="flex items-center gap-3 bg-white/15 hover:bg-white/25 backdrop-blur rounded-2xl px-5 py-4 transition-colors shrink-0"
            >
              <div className="relative">
                <ShoppingCart className="w-6 h-6 text-white" />
                {totalItems > 0 && (
                  <span className="absolute -top-2 -right-2 bg-white text-amber-600 text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center">
                    {totalItems}
                  </span>
                )}
              </div>
              <div className="text-white">
                <div className="font-semibold">Mi Cesta</div>
                <div className="text-amber-200 text-sm">
                  {totalItems === 0
                    ? "Vacía"
                    : `${totalItems} ${totalItems === 1 ? "producto" : "productos"} · ${totalPrice.toFixed(2)} €`}
                </div>
              </div>
            </Link>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="sticky top-16 z-40 bg-white border-b border-amber-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar pan..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent"
            />
          </div>

          {/* Category pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
            <button
              onClick={() => setActiveCategory(ALL)}
              className={cn(
                "shrink-0 text-sm font-medium px-3 py-1.5 rounded-full border transition-all",
                activeCategory === ALL
                  ? "bg-amber-500 text-white border-amber-500"
                  : "border-slate-200 text-slate-600 hover:border-amber-300 hover:text-amber-700"
              )}
            >
              Todos ({BAKERY_PRODUCTS.length})
            </button>
            {categories.map((cat) => {
              const count = BAKERY_PRODUCTS.filter((p) => p.category === cat).length;
              return (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={cn(
                    "shrink-0 text-sm font-medium px-3 py-1.5 rounded-full border transition-all",
                    activeCategory === cat
                      ? "bg-amber-500 text-white border-amber-500"
                      : "border-slate-200 text-slate-600 hover:border-amber-300 hover:text-amber-700"
                  )}
                >
                  {CATEGORY_LABELS[cat]} ({count})
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Product grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {filtered.length === 0 ? (
          <div className="text-center py-20 text-slate-400">
            <div className="text-5xl mb-4">🔍</div>
            <p className="text-lg font-medium">No encontramos ese pan</p>
            <p className="text-sm mt-1">Prueba con otra búsqueda o categoría</p>
          </div>
        ) : (
          <>
            <p className="text-sm text-slate-500 mb-5">
              Mostrando{" "}
              <span className="font-semibold text-slate-700">{filtered.length}</span>{" "}
              {filtered.length === 1 ? "producto" : "productos"}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {filtered.map((product) => (
                <ProductCard key={product.slug} product={product} />
              ))}
            </div>
          </>
        )}

        {/* Info strip */}
        <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-6 border-t border-amber-100 pt-10">
          {[
            {
              emoji: "🌾",
              title: "Ingredientes naturales",
              desc: "Solo harinas de molino, agua, sal y levadura natural. Sin aditivos ni mejorantes artificiales.",
            },
            {
              emoji: "🕕",
              title: "Horneado cada mañana",
              desc: "El pan sale del horno a las 6 de la mañana para que llegue fresco a tu mesa.",
            },
            {
              emoji: "🚚",
              title: "Envío en el día",
              desc: "Pedidos antes de las 9:00 h se entregan ese mismo día. Envío gratis a partir de 30 €.",
            },
          ].map((item) => (
            <div key={item.title} className="flex gap-4 items-start">
              <span className="text-3xl">{item.emoji}</span>
              <div>
                <h3 className="font-semibold text-slate-800">{item.title}</h3>
                <p className="text-sm text-slate-500 mt-0.5">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
