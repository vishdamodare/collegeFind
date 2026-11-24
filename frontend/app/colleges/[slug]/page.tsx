import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { DataBanner, PageHeader, Pill } from "@/components/Chrome";
import BranchBlock from "@/components/BranchTrend";
import { ApiError, get, Meta } from "@/lib/api";

type College = { name: string; slug: string; institute_code: string; ownership: string | null; status_raw: string | null; university: string | null; website: string | null; branches: { name: string; choice_code: string; cutoff_years: string[]; intake: null | { year: string; si: number; ms_seats: number; minority_seats: number; all_india_seats: number; institute_seats: number; orphan_seats: number; published_date: string | null; source_page: number | null } }[] };

async function load(slug: string) {
  try { return await get<College>(`/api/v1/colleges/${slug}`); } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;  // genuinely missing
    throw e;  // outage / timeout / 5xx must not masquerade as "not found"
  }
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const c = await load((await params).slug);
  return c ? { title: c.name, description: `Branches and official historical CAP cutoffs for ${c.name} (code ${c.institute_code}).` } : {};
}

export default async function CollegePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [c, meta] = await Promise.all([load(slug), get<Meta>("/api/v1/meta")]);
  if (!c) notFound();
  const latest = c.branches.reduce((m, b) => (b.intake && b.intake.year > m ? b.intake.year : m), "");
  const inLatest = c.branches.filter((b) => b.intake?.year === latest);
  const total = latest ? { year: latest, sum: inLatest.reduce((a, b) => a + (b.intake?.si ?? 0), 0), n: inLatest.length } : null;
  return (
    <main>
      <PageHeader title={c.name} crumb={<Link href="/colleges" className="hover:text-brand-ink">← All colleges</Link>}>
        <div className="flex flex-wrap gap-2">
          <Pill>Code {c.institute_code}</Pill>
          {c.status_raw && <Pill>{c.status_raw}</Pill>}
          {c.university && <Pill>{c.university}</Pill>}
        </div>
      </PageHeader>
      <div className="mx-auto max-w-6xl px-4 py-5 md:py-8">
        <DataBanner meta={meta} />

        <dl className="card mt-5 grid grid-cols-3 divide-x divide-line">
          {[[total ? total.sum.toLocaleString() : "—", total ? `CAP seats · ${total.year}` : "CAP seats"], [String(c.branches.length), "Branches"], [c.ownership ?? "—", "Type"]].map(([v, l]) => (
            <div key={l} className="flex flex-col-reverse px-3 py-3.5 md:px-5 md:py-4">
              <dt className="mt-0.5 text-xs text-muted">{l}</dt>
              <dd className="num text-xl font-bold capitalize md:text-2xl">{v}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 text-xs text-muted">Fees, placements, address and rankings aren&apos;t available yet. We only show data from official sources.</p>

        <h2 className="mt-10 text-xl font-bold tracking-tight md:text-2xl">Branches <span className="text-muted">({c.branches.length})</span></h2>
        <ul className="card mt-3 divide-y divide-line overflow-hidden">
          {c.branches.map((b) => (
            <li key={b.choice_code} className="p-4 md:p-5">
              <BranchBlock slug={c.slug} code={b.choice_code} hasTrend={(b.cutoff_years ?? []).length > 0}
                href={`/cutoffs?college=${c.slug}&branch=${encodeURIComponent(b.name)}`}
                left={<div className="min-w-0"><p className="font-semibold leading-snug">{b.name}</p><p className="mt-0.5 text-xs text-muted">Code {b.choice_code}{(b.cutoff_years ?? []).length ? ` · cutoffs ${(b.cutoff_years ?? []).map((y) => y.slice(0, 4)).join(", ")}` : " · no cutoff records"}</p></div>}
                intake={b.intake ? (
                  <p className="mt-2 text-xs text-muted">
                    <b className="num text-navy">{b.intake.si} seats</b> ({b.intake.year}): Maharashtra {b.intake.ms_seats} · Minority {b.intake.minority_seats} · All India {b.intake.all_india_seats} · Institute {b.intake.institute_seats}
                  </p>
                ) : <p className="mt-2 text-xs text-muted">Seat count not published</p>} />
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
