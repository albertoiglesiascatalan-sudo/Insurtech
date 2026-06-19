"use client";

import Link from "next/link";
import { ShoppingCart, Check } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useCart } from "./CartContext";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/bakery-data";
import type { BakeryProduct } from "@/lib/bakery-data";

interface ProductCardProps {
  product: BakeryProduct;
}

export function ProductCard({ product }: ProductCardProps) {
  const { addToCart } = useCart();
  const [added, setAdded] = useState(false);

  function handleAdd(e: React.MouseEvent) {
    e.preventDefault();
    addToCart(product);
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  }

  return (
    <Link
      href={`/bakery/${product.slug}`}
      className="group flex flex-col bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-lg hover:border-amber-200 transition-all duration-200"
    >
      {/* Product image area */}
      <div
        className={cn(
          "relative h-44 flex items-center justify-center text-7xl bg-gradient-to-br",
          product.gradient
        )}
      >
        <span className="drop-shadow-sm">{product.emoji}</span>
        {product.featured && (
          <span className="absolute top-3 left-3 bg-amber-500 text-white text-xs font-bold px-2 py-1 rounded-full">
            Destacado
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-col flex-1 p-4 gap-2">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-slate-900 group-hover:text-amber-700 transition-colors leading-tight">
            {product.name}
          </h3>
          <span
            className={cn(
              "shrink-0 text-xs font-medium px-2 py-0.5 rounded-full",
              CATEGORY_COLORS[product.category]
            )}
          >
            {CATEGORY_LABELS[product.category]}
          </span>
        </div>

        <p className="text-sm text-slate-500 leading-relaxed line-clamp-2 flex-1">
          {product.description}
        </p>

        <div className="flex items-center gap-1 flex-wrap mt-1">
          {product.tags.slice(0, 2).map((tag) => (
            <span
              key={tag}
              className="text-xs text-slate-400 bg-slate-50 border border-slate-100 px-2 py-0.5 rounded-full"
            >
              {tag}
            </span>
          ))}
          <span className="text-xs text-slate-400 ml-auto">{product.weight}</span>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 mt-1">
          <div>
            <span className="text-xl font-bold text-slate-900">
              {product.price.toFixed(2)} €
            </span>
            <span className="text-xs text-slate-400 ml-1">/ {product.unit}</span>
          </div>
          <button
            onClick={handleAdd}
            className={cn(
              "flex items-center gap-1.5 text-sm font-semibold px-3 py-2 rounded-xl transition-all duration-200",
              added
                ? "bg-green-100 text-green-700"
                : "bg-amber-500 hover:bg-amber-600 text-white"
            )}
          >
            {added ? (
              <>
                <Check className="w-4 h-4" />
                Añadido
              </>
            ) : (
              <>
                <ShoppingCart className="w-4 h-4" />
                Añadir
              </>
            )}
          </button>
        </div>
      </div>
    </Link>
  );
}
