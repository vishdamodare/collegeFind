import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-xl px-4 py-24 text-center">
      <p className="text-sm font-semibold uppercase tracking-wider text-brand-ink">404</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">We couldn&apos;t find that page</h1>
      <p className="mt-3 text-navy/65">The college or page you asked for isn&apos;t in our data. It may have been renamed, or the data may still be loading.</p>
      <div className="mt-8 flex justify-center gap-3">
        <Link href="/colleges" className="rounded-xl bg-navy px-6 py-3 font-semibold text-white hover:bg-navy-2">Browse colleges</Link>
        <Link href="/" className="rounded-xl border border-navy/20 px-6 py-3 font-semibold hover:bg-navy/5">Home</Link>
      </div>
    </main>
  );
}
