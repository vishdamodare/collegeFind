"use client";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="mx-auto max-w-xl px-4 py-24 text-center">
      <p className="text-sm font-semibold uppercase tracking-wider text-brand-ink">Something went wrong</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">We couldn&apos;t load this page</h1>
      <p className="mt-3 text-navy/65">Our data service didn&apos;t respond. This is usually temporary — please try again.</p>
      <button onClick={reset} className="mt-8 rounded-xl bg-navy px-6 py-3 font-semibold text-white hover:bg-navy-2">Try again</button>
    </main>
  );
}
