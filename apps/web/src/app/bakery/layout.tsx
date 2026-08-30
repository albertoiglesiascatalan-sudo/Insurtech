import { CartProvider } from "@/components/bakery/CartContext";
import { ReactNode } from "react";

export default function BakeryLayout({ children }: { children: ReactNode }) {
  return <CartProvider>{children}</CartProvider>;
}
