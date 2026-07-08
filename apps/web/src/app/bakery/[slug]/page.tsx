"use client";

import { notFound } from "next/navigation";
import Link from "next/link";
import { use, useState } from "react";
import {
  ArrowLeft,
  ShoppingCart,
  Check,
  Minus,
  Plus,
  AlertCircle,
  Package,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCart } from "@/components/bakery/CartContext";
import {
  getProduct,
  CATEGORY_LABELS,
  CATEGORY_COLORS,
} from "@/lib/bakery-data";

export default function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const product = getProduct(slug);

  if (!product) notFound();

  return <ProductDetail slug={slug} />;
}

function ProductDetail({ slug }: { slug: string }) {
  const product = getProduct(slug)!;
  const { addToCart, items, updateQuantity, removeFromCart } = useCart();
  const [added, setAdded] = useState(false);

  const cartItem = items.find((i) => i.product.slug === product.slug);
  const qty = cartItem?.quantity ?? 0;

  function handleAdd() {
    addToCart(product);
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  }

  return (
    <div className="min-h-screen bg-amber-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-slate-500 mb-8">
          <Link href="/bakery" className="flex items-center gap-1 hover:text-amber-600 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Tienda
          </Link>
          <span>/</span>
          <span className="text-slate-900 font-medium">{product.name}</span>
        </nav>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {/* Visual */}
          <div className="space-y-4">
            <div
              className={cn(
                "rounded-3xl h-72 flex items-center justify-center text-9xl bg-gradient-to-br shadow-inner",
                product.gradient
              )}
            >
              {product.emoji}
            </div>
            {product.featured && (
              <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
                <span className="text-amber-500 font-bold text-sm">★ Producto destacado</span>
                <span className="text-amber-600 text-sm">— uno de nuestros más vendidos</span>
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex flex-col gap-5">
            <div>
              <span
                className={cn(
                  "text-xs font-medium px-2.5 py-1 rounded-full",
                  CATEGORY_COLORS[product.category]
                )}
              >
                {CATEGORY_LABELS[product.category]}
              </span>
              <h1 className="text-3xl font-bold text-slate-900 mt-3">
                {product.name}
              </h1>
              <p className="text-slate-600 mt-2 leading-relaxed">
                {product.longDescription}
              </p>
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-2">
              {product.tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs text-slate-500 bg-white border border-slate-200 px-3 py-1 rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>

            {/* Weight */}
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Package className="w-4 h-4" />
              <span>Peso: <strong className="text-slate-700">{product.weight}</strong></span>
            </div>

            {/* Price */}
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-slate-900">
                {product.price.toFixed(2)} €
              </span>
              <span className="text-slate-400">/ {product.unit}</span>
            </div>

            {/* Add to cart */}
            {qty === 0 ? (
              <button
                onClick={handleAdd}
                className={cn(
                  "flex items-center justify-center gap-2 font-semibold py-3.5 rounded-2xl transition-all duration-200 text-base",
                  added
                    ? "bg-green-100 text-green-700"
                    : "bg-amber-500 hover:bg-amber-600 text-white"
                )}
              >
                {added ? (
                  <>
                    <Check className="w-5 h-5" />
                    Añadido a la cesta
                  </>
                ) : (
                  <>
                    <ShoppingCart className="w-5 h-5" />
                    Añadir a la cesta
                  </>
                )}
              </button>
            ) : (
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 bg-white border border-amber-200 rounded-2xl px-2 py-1">
                  <button
                    onClick={() => {
                      if (qty === 1) removeFromCart(product.slug);
                      else updateQuantity(product.slug, qty - 1);
                    }}
                    className="p-2 hover:bg-amber-50 rounded-xl transition-colors"
                  >
                    <Minus className="w-4 h-4 text-amber-600" />
                  </button>
                  <span className="w-8 text-center font-bold text-slate-900">{qty}</span>
                  <button
                    onClick={() => updateQuantity(product.slug, qty + 1)}
                    className="p-2 hover:bg-amber-50 rounded-xl transition-colors"
                  >
                    <Plus className="w-4 h-4 text-amber-600" />
                  </button>
                </div>
                <Link
                  href="/bakery/cart"
                  className="flex-1 text-center bg-amber-500 hover:bg-amber-600 text-white font-semibold py-3.5 rounded-2xl transition-colors"
                >
                  Ver cesta →
                </Link>
              </div>
            )}

            {/* Allergens */}
            {product.allergens.length > 0 && (
              <div className="flex items-start gap-2 bg-orange-50 border border-orange-200 rounded-xl p-3 text-sm text-orange-700">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <div>
                  <span className="font-semibold">Alérgenos: </span>
                  {product.allergens.join(", ")}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Ingredients */}
        <div className="mt-12 bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Ingredientes</h2>
          <div className="flex flex-wrap gap-2">
            {product.ingredients.map((ing) => (
              <span
                key={ing}
                className="text-sm bg-amber-50 border border-amber-100 text-amber-800 px-3 py-1.5 rounded-full"
              >
                {ing}
              </span>
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-4">
            * Elaborado en un obrador donde se manipulan cereales, frutos secos, lácteos y huevo.
          </p>
        </div>
      </div>
    </div>
  );
}
