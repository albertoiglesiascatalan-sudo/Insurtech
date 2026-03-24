import { Suspense } from "react";
import Link from "next/link";
import { SubscribeForm } from "@/components/newsletter/SubscribeForm";
import { CheckCircle } from "lucide-react";

export const metadata = {
  title: "Subscribe — Free Newsletter",
  description: "Get the best insurtech newsletter. Daily or weekly digest, personalised for investors, founders or general professionals.",
};

const BENEFITS = [
  "55+ global sources in one place",
  "AI-powered summaries (no fluff)",
  "Deduplicated — no repeated stories",
  "Investor, Founder or General edition",
  "Daily or weekly digest options",
  "Free forever, unsubscribe anytime",
];

export default function NewsletterPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
        {/* Left: value prop */}
        <div>
          <h1 className="text-4xl font-bold text-slate-900 mb-4 leading-tight">
            The best insurtech newsletter.<br />
            <span className="text-brand">Free.</span>
          </h1>
          <p className="text-lg text-slate-600 mb-8">
            Global insurtech intelligence from 55+ verified sources, AI-summarised and
            personalised to your profile. Join thousands of professionals reading InsurTech Intelligence.
          </p>

          <ul className="space-y-3 mb-8">
            {BENEFITS.map((b) => (
              <li key={b} className="flex items-center gap-3 text-slate-700">
                <CheckCircle className="w-5 h-5 text-brand shrink-0" />
                <span>{b}</span>
              </li>
            ))}
          </ul>

          <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200">
            <p className="text-sm text-slate-500 font-medium mb-2">Recent editions</p>
            <Link href="/newsletter/archive" className="text-brand text-sm hover:underline font-semibold">
              Browse past newsletters →
            </Link>
          </div>
        </div>

        {/* Right: form */}
        <div>
          <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
            <h2 className="text-xl font-bold text-slate-900 mb-6">
              Subscribe — it's free
            </h2>
            <Suspense>
              <SubscribeForm />
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}
