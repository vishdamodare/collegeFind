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
      <div className="mx-auto max-w-6xl px-4 py-8">
        <DataBanner meta={meta} />

        <dl className="mt-6 grid grid-cols-3 gap-px overflow-hidden rounded-2xl bg-navy/10 text-sm shadow-[var(--shadow-card)]">
          <div className="bg-white p-4">
            <dt className="text-xs font-medium uppercase tracking-wide text-navy/50">Total seats{total ? ` · ${total.year}` : ""}</dt>
            <dd className={total ? "mt-1 text-lg font-bold" : "mt-1 text-navy/50"}>{total ? `${total.sum} seats` : "Data not available"}</dd>
            {total && <p className="mt-0.5 text-xs text-navy/55">Across {total.n} branches (CAP seat matrix)</p>}
          </div>
          <div className="bg-white p-4">
            <dt className="text-xs font-medium uppercase tracking-wide text-navy/50">Branches</dt>
            <dd className="mt-1 text-lg font-bold">{c.branches.length}</dd>
          </div>
          <div className="bg-white p-4">
            <dt className="text-xs font-medium uppercase tracking-wide text-navy/50">Type</dt>
            <dd className="mt-1 font-semibold capitalize">{c.ownership ?? "—"}</dd>
          </div>
        </dl>
        <p className="mt-3 text-xs text-muted">Fees, placements, address and rankings aren&apos;t available yet — we only show data from official sources.</p>

        <h2 className="mt-12 text-2xl font-bold tracking-tight">Branches <span className="text-navy/40">({c.branches.length})</span></h2>
        <ul className="mt-4 divide-y divide-line overflow-hidden rounded-2xl border border-line bg-white shadow-[var(--shadow-card)]">
          {c.branches.map((b) => (
            <li key={b.choice_code} className="p-4 transition hover:bg-navy/[.02]">
              <BranchBlock slug={c.slug} code={b.choice_code} hasTrend={(b.cutoff_years ?? []).length > 0}
                href={`/cutoffs?college=${c.slug}&branch=${encodeURIComponent(b.name)}`}
                left={<div><p className="font-medium">{b.name}</p><p className="text-xs text-navy/55">Choice code {b.choice_code}{(b.cutoff_years ?? []).length ? ` · cutoffs: ${(b.cutoff_years ?? []).join(", ")}` : " · no cutoff records"}</p></div>}
                intake={b.intake ? (
                  <p className="mt-2 text-xs text-navy/65">
                    <b className="text-navy">{b.intake.si} seats</b> <span className="text-navy/55">({b.intake.year})</span> — Maharashtra {b.intake.ms_seats} · Minority {b.intake.minority_seats} · All India {b.intake.all_india_seats} · Institute {b.intake.institute_seats}
                  </p>
                ) : <p className="mt-2 text-xs text-navy/45">Seat count not published</p>} />
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
