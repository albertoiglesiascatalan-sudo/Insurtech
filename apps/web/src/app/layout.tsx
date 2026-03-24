import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: {
    default: "InsurTech Intelligence — Global Newsletter",
    template: "%s | InsurTech Intelligence",
  },
  description:
    "The best insurtech newsletter: global news from 55+ verified sources, filtered by topic, region and reader profile. AI-powered summaries.",
  keywords: ["insurtech", "insurance technology", "newsletter", "fintech", "embedded insurance"],
  openGraph: {
    siteName: "InsurTech Intelligence",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Header />
        <main className="min-h-screen">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
