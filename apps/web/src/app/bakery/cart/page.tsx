"use client";

import Link from "next/link";
import { ArrowLeft, Trash2, Minus, Plus, ShoppingBag, Wheat } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCart } from "@/components/bakery/CartContext";
import { useState } from "react";

export default function CartPage() {
  const { items, totalItems, totalPrice, updateQuantity, removeFromCart, clearCart } =
    useCart();
  const [ordered, setOrdered] = useState(false);

  const shipping = totalPrice >= 30 ? 0 : 3.5;
  const grandTotal = totalPrice + shipping;

  function handleOrder() {
    clearCart();
    setOrdered(true);
  }

  if (ordered) {
    return (
      <div className="min-h-screen bg-amber-50 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-7xl mb-6">🎉</div>
          <h1 className="text-3xl font-bold text-slate-900 mb-3">
            ¡Pedido confirmado!
          </h1>
          <p className="text-slate-600 mb-6">
            Gracias por tu pedido. Lo preparamos esta misma noche y lo tendrás
            recién horneado mañana por la mañana.
          </p>
          <div className="bg-white border border-amber-100 rounded-2xl p-5 mb-6 text-sm text-slate-600 space-y-2">
            <div className="flex items-center gap-2">
              <span>🕕</span>
              <span>Horneado: mañana a las 6:00 h</span>
            </div>
            <div className="flex items-center gap-2">
              <span>🚚</span>
              <span>Entrega: mañana entre 8:00 y 11:00 h</span>
            </div>
            <div className="flex items-center gap-2">
              <span>📧</span>
              <span>Recibirás un email de confirmación</span>
            </div>
          </div>
          <Link
            href="/bakery"
            className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-semibold px-6 py-3 rounded-2xl transition-colors"
          >
            <Wheat className="w-4 h-4" />
            Seguir comprando
          </Link>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-amber-50 flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <div className="text-7xl mb-6">🛒</div>
          <h1 className="text-2xl font-bold text-slate-900 mb-3">Tu cesta está vacía</h1>
          <p className="text-slate-500 mb-6">
            Todavía no has añadido ningún pan. Echa un vistazo a nuestro obrador.
          </p>
          <Link
            href="/bakery"
            className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-semibold px-6 py-3 rounded-2xl transition-colors"
          >
            <Wheat className="w-4 h-4" />
            Ver productos
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <div className="bg-white border-b border-amber-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <nav className="flex items-center gap-2 text-sm text-slate-500 mb-4">
            <Link href="/bakery" className="flex items-center gap-1 hover:text-amber-600 transition-colors">
              <ArrowLeft className="w-4 h-4" />
              Seguir comprando
            </Link>
          </nav>
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-slate-900">
              Mi Cesta{" "}
              <span className="text-slate-400 font-normal text-lg">
                ({totalItems} {totalItems === 1 ? "producto" : "productos"})
              </span>
            </h1>
            <button
              onClick={clearCart}
              className="text-xs text-slate-400 hover:text-red-500 transition-colors flex items-center gap-1"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Vaciar cesta
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart items */}
          <div className="lg:col-span-2 space-y-3">
            {items.map(({ product, quantity }) => (
              <div
                key={product.slug}
                className="bg-white rounded-2xl border border-slate-200 p-4 flex items-center gap-4"
              >
                {/* Thumbnail */}
                <div
                  className={cn(
                    "w-16 h-16 rounded-xl flex items-center justify-center text-3xl bg-gradient-to-br shrink-0",
                    product.gradient
                  )}
                >
                  {product.emoji}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/bakery/${product.slug}`}
                    className="font-semibold text-slate-900 hover:text-amber-600 transition-colors truncate block"
                  >
                    {product.name}
                  </Link>
                  <p className="text-sm text-slate-400">{product.weight} · {product.unit}</p>
                  <p className="text-sm font-bold text-amber-600 mt-0.5">
                    {(product.price * quantity).toFixed(2)} €
                  </p>
                </div>

                {/* Quantity */}
                <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 rounded-xl px-1 py-1">
                  <button
                    onClick={() => {
                      if (quantity === 1) removeFromCart(product.slug);
                      else updateQuantity(product.slug, quantity - 1);
                    }}
                    className="p-1.5 hover:bg-amber-100 rounded-lg transition-colors"
                  >
                    <Minus className="w-3.5 h-3.5 text-slate-600" />
                  </button>
                  <span className="w-7 text-center text-sm font-semibold text-slate-900">
                    {quantity}
                  </span>
                  <button
                    onClick={() => updateQuantity(product.slug, quantity + 1)}
                    className="p-1.5 hover:bg-amber-100 rounded-lg transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5 text-slate-600" />
                  </button>
                </div>

                {/* Remove */}
                <button
                  onClick={() => removeFromCart(product.slug)}
                  className="p-2 text-slate-300 hover:text-red-400 hover:bg-red-50 rounded-xl transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Order summary */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl border border-slate-200 p-5 sticky top-24 space-y-4">
              <h2 className="font-bold text-slate-900 text-lg">Resumen del pedido</h2>

              <div className="space-y-2 text-sm">
                {items.map(({ product, quantity }) => (
                  <div key={product.slug} className="flex justify-between text-slate-600">
                    <span className="truncate mr-2">
                      {product.name} × {quantity}
                    </span>
                    <span className="shrink-0 font-medium">
                      {(product.price * quantity).toFixed(2)} €
                    </span>
                  </div>
                ))}
              </div>

              <div className="border-t border-slate-100 pt-3 space-y-2 text-sm">
                <div className="flex justify-between text-slate-600">
                  <span>Subtotal</span>
                  <span>{totalPrice.toFixed(2)} €</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Envío</span>
                  {shipping === 0 ? (
                    <span className="text-green-600 font-medium">Gratis</span>
                  ) : (
                    <span>{shipping.toFixed(2)} €</span>
                  )}
                </div>
                {shipping > 0 && (
                  <p className="text-xs text-amber-600">
                    Añade {(30 - totalPrice).toFixed(2)} € más para envío gratis
                  </p>
                )}
              </div>

              <div className="border-t border-slate-100 pt-3 flex justify-between font-bold text-slate-900">
                <span>Total</span>
                <span>{grandTotal.toFixed(2)} €</span>
              </div>

              <button
                onClick={handleOrder}
                className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-semibold py-3.5 rounded-2xl transition-colors"
              >
                <ShoppingBag className="w-5 h-5" />
                Realizar pedido
              </button>

              <p className="text-xs text-slate-400 text-center">
                Pago seguro · Devolución en 24 h
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
