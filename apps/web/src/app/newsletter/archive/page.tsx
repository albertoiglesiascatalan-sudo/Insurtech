export const metadata = {
  title: "Newsletter Archive",
  description: "Browse past editions of InsurTech Intelligence.",
};

export default function ArchivePage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-slate-900 mb-2">Newsletter Archive</h1>
      <p className="text-slate-600 mb-8">Browse past editions of InsurTech Intelligence.</p>
      <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-400">
        <p className="text-lg font-medium mb-2">No issues yet</p>
        <p className="text-sm">Newsletter editions will appear here once sent.</p>
      </div>
    </div>
  );
}
