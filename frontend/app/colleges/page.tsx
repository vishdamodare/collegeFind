import type { Metadata } from "next";
import Link from "next/link";
import { DataBanner, PageHeader, Pill } from "@/components/Chrome";
import { get, Meta } from "@/lib/api";

export const metadata: Metadata = { title: "Find Colleges" };
type Res = { total: number; page: number; page_size: number; items: { name: string; slug: string; institute_code: string; ownership: string | null; status_raw: string | null; university: string | null; branches: number }[] };
const TONE = { government: "green", aided: "amber", unaided: "navy" } as const;

export default async function Colleges({ searchParams }: { searchParams: Promise<{ q?: string; ownership?: string; page?: string }> }) {
  const sp = await searchParams;
  const page = Math.max(1, Number(sp.page ?? 1));
  const qs = new URLSearchParams({ page: String(page) });
  if (sp.q) qs.set("q", sp.q);
  if (sp.ownership) qs.set("ownership", sp.ownership);
  const [data, meta] = await Promise.all([get<Res>(`/api/v1/colleges?${qs}`), get<Meta>("/api/v1/meta")]);
  const pages = Math.ceil(data.total / data.page_size);
  const link = (p: number) => `/colleges?${new URLSearchParams({ ...(sp.q ? { q: sp.q } : {}), ...(sp.ownership ? { ownership: sp.ownership } : {}), page: String(p) })}`;

  return (
    <main>
      <PageHeader title="Find Colleges">{data.total.toLocaleString()} colleges in the CET Cell cutoff list. Open one to see its branches and cutoffs.</PageHeader>
      <div className="mx-auto max-w-6xl px-4 py-8">
        <DataBanner meta={meta} />
        <form className="mt-6 flex flex-wrap gap-3 rounded-2xl border border-line bg-white p-3 shadow-[var(--shadow-card)]" role="search">
          <label className="sr-only" htmlFor="q">Search by college name or code</label>
          <input id="q" name="q" defaultValue={sp.q} placeholder="Search by college name or 5-digit code…" className="min-w-64 flex-1 rounded-xl border border-navy/15 px-4 py-2.5 outline-none focus:border-brand focus:ring-4 focus:ring-brand/15" />
          <label className="sr-only" htmlFor="own">Type</label>
          <select id="own" name="ownership" defaultValue={sp.ownership ?? ""} className="rounded-xl border border-navy/15 bg-white px-3 py-2.5">
            <option value="">All types</option><option value="government">Government</option><option value="aided">Aided</option><option value="unaided">Un-aided</option>
          </select>
          <button className="rounded-xl bg-navy px-6 py-2.5 font-semibold text-white hover:bg-navy-2">Search</button>
        </form>

        <ul className="mt-6 grid gap-4 md:grid-cols-2">
          {data.items.map((c) => (
            <li key={c.slug}>
              <Link href={`/colleges/${c.slug}`} className="flex h-full gap-4 rounded-2xl border border-line bg-white p-5 shadow-[var(--shadow-card)] transition hover:border-navy">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-navy text-base font-bold text-brand" aria-hidden>{c.name.charAt(0)}</span>
                <div className="min-w-0">
                  <p className="font-semibold leading-snug">{c.name}</p>
                  <p className="mt-1 text-sm text-navy/60">Code {c.institute_code} · {c.branches} branches</p>
                  {c.university && <p className="text-sm text-navy/60">{c.university}</p>}
                  <div className="mt-2.5 flex flex-wrap gap-2">
                    {c.status_raw && <Pill tone={c.ownership ? TONE[c.ownership as keyof typeof TONE] : "navy"}>{c.status_raw}</Pill>}
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
        {data.items.length === 0 && <p className="mt-10 text-center text-navy/70">No colleges match your search.</p>}

        {pages > 1 && (
          <nav aria-label="Pagination" className="mt-10 flex items-center justify-between text-sm">
            {page > 1 ? <Link href={link(page - 1)} className="rounded-xl border border-navy/20 bg-white px-5 py-2.5 font-medium">← Previous</Link> : <span />}
            <span className="text-navy/60">Page {page} of {pages}</span>
            {page < pages ? <Link href={link(page + 1)} className="rounded-xl border border-navy/20 bg-white px-5 py-2.5 font-medium">Next →</Link> : <span />}
          </nav>
        )}
      </div>
    </main>
  );
}
