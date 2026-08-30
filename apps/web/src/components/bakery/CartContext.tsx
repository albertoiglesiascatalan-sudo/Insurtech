"use client";

import {
  createContext,
  useContext,
  useEffect,
  useReducer,
  ReactNode,
} from "react";
import type { BakeryProduct } from "@/lib/bakery-data";

export interface CartItem {
  product: BakeryProduct;
  quantity: number;
}

interface CartState {
  items: CartItem[];
}

type CartAction =
  | { type: "ADD"; product: BakeryProduct }
  | { type: "REMOVE"; slug: string }
  | { type: "UPDATE_QTY"; slug: string; quantity: number }
  | { type: "CLEAR" }
  | { type: "HYDRATE"; items: CartItem[] };

function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case "ADD": {
      const existing = state.items.find(
        (i) => i.product.slug === action.product.slug
      );
      if (existing) {
        return {
          items: state.items.map((i) =>
            i.product.slug === action.product.slug
              ? { ...i, quantity: i.quantity + 1 }
              : i
          ),
        };
      }
      return { items: [...state.items, { product: action.product, quantity: 1 }] };
    }
    case "REMOVE":
      return { items: state.items.filter((i) => i.product.slug !== action.slug) };
    case "UPDATE_QTY": {
      if (action.quantity <= 0) {
        return { items: state.items.filter((i) => i.product.slug !== action.slug) };
      }
      return {
        items: state.items.map((i) =>
          i.product.slug === action.slug ? { ...i, quantity: action.quantity } : i
        ),
      };
    }
    case "CLEAR":
      return { items: [] };
    case "HYDRATE":
      return { items: action.items };
    default:
      return state;
  }
}

interface CartContextValue {
  items: CartItem[];
  totalItems: number;
  totalPrice: number;
  addToCart: (product: BakeryProduct) => void;
  removeFromCart: (slug: string) => void;
  updateQuantity: (slug: string, quantity: number) => void;
  clearCart: () => void;
}

const CartContext = createContext<CartContextValue | null>(null);

const STORAGE_KEY = "bakery-cart";

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, { items: [] });

  // Hydrate from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as CartItem[];
        dispatch({ type: "HYDRATE", items: parsed });
      }
    } catch {
      // ignore corrupt data
    }
  }, []);

  // Persist on every change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state.items));
    } catch {
      // ignore storage errors
    }
  }, [state.items]);

  const totalItems = state.items.reduce((sum, i) => sum + i.quantity, 0);
  const totalPrice = state.items.reduce(
    (sum, i) => sum + i.product.price * i.quantity,
    0
  );

  return (
    <CartContext.Provider
      value={{
        items: state.items,
        totalItems,
        totalPrice,
        addToCart: (product) => dispatch({ type: "ADD", product }),
        removeFromCart: (slug) => dispatch({ type: "REMOVE", slug }),
        updateQuantity: (slug, quantity) =>
          dispatch({ type: "UPDATE_QTY", slug, quantity }),
        clearCart: () => dispatch({ type: "CLEAR" }),
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
