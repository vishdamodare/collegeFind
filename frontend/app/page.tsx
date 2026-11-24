import Link from "next/link";
import { get, Meta } from "@/lib/api";

const CATEGORIES: [string, string][] = [
  ["GOPENS", "Open"], ["GOBCS", "OBC"], ["GSEBCS", "SEBC"], ["EWS", "EWS"], ["GSCS", "SC"], ["GSTS", "ST"],
  ["GVJS", "VJ / DT-A"], ["GNT1S", "NT-B"], ["GNT2S", "NT-C"], ["GNT3S", "NT-D"],
];

const FAQ = [
  ["Does this predict my admission?", "No. It shows how your percentile compares with where seats closed in earlier CAP rounds. Cutoffs change every year, so nothing here is a guarantee."],
  ["Where does the data come from?", "Only from the cutoff lists and seat matrices published by the Maharashtra State CET Cell. Every number links to its source PDF page."],
  ["Why do some values say “Data not available”?", "We never estimate. If the official list has no value, we say so."],
  ["Do I need to sign up?", "No. Everything is free and works without an account."],
];

async function stats() {
  try {
    const [m, c] = await Promise.all([get<Meta>("/api/v1/meta"), get<{ total: number }>("/api/v1/colleges?page_size=1")]);
    const records = Object.values(m.records).reduce((a, b) => a + b, 0);
    const span = m.years.length ? `${m.years[0].slice(0, 4)}–${m.years[m.years.length - 1].slice(0, 4)}` : "";
    return { colleges: c.total, records, years: String(m.years.length), span };
  } catch { return null; }
}

const ICONS = {
  target: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.5" fill="currentColor" /></>,
  table: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M9 10v10" /></>,
  building: <><path d="M3 21h18M5 21V8l7-4 7 4v13" /><path d="M9 21v-5h6v5M9 11h.01M15 11h.01" /></>,
};
function Icon({ name }: { name: keyof typeof ICONS }) {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>{ICONS[name]}</svg>;
}

export default async function Home() {
  const s = await stats();
  return (
    <main>
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div aria-hidden className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_55%_at_80%_0%,rgb(255_102_0/0.16),transparent_70%),radial-gradient(40%_40%_at_5%_55%,rgb(255_169_77/0.12),transparent_70%)]" />
        <div className="relative mx-auto max-w-6xl px-4 pb-12 pt-10 md:pb-20 md:pt-20">
          <div className="mx-auto max-w-3xl text-center">
            <p className="rise inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-muted ring-1 ring-line">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Free · Official MHT-CET CAP data
            </p>
            <h1 className="rise rise-2 mt-5 text-[36px] font-bold leading-[1.06] tracking-tight sm:text-5xl md:text-[64px]">
              Got your percentile?<br />Find your <span className="text-brand">college.</span>
            </h1>
            <p className="rise rise-3 mx-auto mt-4 max-w-xl text-base leading-relaxed text-muted md:text-lg">
              Enter your score. See where students like you got in.
            </p>
          </div>

          <form action="/predictor" className="rise rise-3 mx-auto mt-8 max-w-2xl rounded-2xl bg-white p-3 shadow-[0_20px_50px_-20px_rgb(28_28_28/0.25)] ring-1 ring-line md:mt-10 md:p-4">
            <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
              <label className="block text-left">
                <span className="mb-1 block px-1 text-xs font-semibold text-muted">Your percentile</span>
                <input name="percentile" type="number" inputMode="decimal" min="0" max="100" step="0.0000001" required placeholder="e.g. 92.5"
                  className="field num h-12 text-lg" />
              </label>
              <label className="block text-left">
                <span className="mb-1 block px-1 text-xs font-semibold text-muted">Your category</span>
                <select name="category" defaultValue="GOPENS" className="field h-12">
                  {CATEGORIES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <button className="h-12 self-end rounded-xl bg-brand px-6 font-bold text-navy transition hover:brightness-95 active:scale-[.98]">
                Show colleges →
              </button>
            </div>
          </form>
          <p className="mt-4 text-center text-sm text-muted">
            or browse <Link href="/colleges" className="font-semibold text-navy underline decoration-brand decoration-2 underline-offset-4">all colleges</Link>
            {" "}·{" "}<Link href="/cutoffs" className="font-semibold text-navy underline decoration-brand decoration-2 underline-offset-4">every cutoff</Link>
          </p>

          {s && (
            <dl className="mx-auto mt-10 grid max-w-2xl grid-cols-3 divide-x divide-line text-center md:mt-14">
              {[[s.colleges.toLocaleString(), "colleges"], [s.records.toLocaleString(), "official cutoffs"], [s.years, `CAP years · ${s.span}`]].map(([v, l]) => (
                <div key={l} className="flex flex-col-reverse px-2">
                  <dt className="mt-1 text-xs text-muted md:text-sm">{l}</dt>
                  <dd className="num text-xl font-bold md:text-3xl">{v}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </section>

      {/* WHAT YOU CAN DO */}
      <section className="mx-auto max-w-6xl px-4">
        <ul className="grid gap-3 md:grid-cols-3 md:gap-4">
          {([
            ["/predictor", "target", "College predictor", "See safer, close and reach options for your percentile and category."],
            ["/cutoffs", "table", "Cutoff explorer", "Every closing cutoff by branch, category, year and round."],
            ["/colleges", "building", "College profiles", "Branches, seats and cutoff trends for every college in the CAP lists."],
          ] as const).map(([h, icon, t, d]) => (
            <li key={h}>
              <Link href={h} className="card group flex h-full items-start gap-4 p-5 transition hover:-translate-y-0.5 hover:border-navy/30 hover:shadow-[0_12px_30px_-18px_rgb(28_28_28/0.35)]">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand/10 text-brand-ink"><Icon name={icon} /></span>
                <span className="min-w-0">
                  <span className="flex items-center gap-1.5 font-bold">{t}<span aria-hidden className="text-muted transition group-hover:translate-x-0.5 group-hover:text-brand-ink">→</span></span>
                  <span className="mt-1 block text-sm leading-relaxed text-muted">{d}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* HOW IT WORKS */}
      <section className="mx-auto mt-16 max-w-6xl px-4 md:mt-24">
        <h2 className="text-center text-2xl font-bold tracking-tight md:text-3xl">How it works</h2>
        <ol className="mt-8 grid gap-6 md:grid-cols-3 md:gap-8">
          {[["Enter your score", "Your MHT-CET percentile and category. That's all."],
            ["We compare with history", "Your score is matched against official closing cutoffs from past CAP rounds."],
            ["Pick with confidence", "Results are grouped into safer, close and reach, each linked to its official source page."]].map(([t, d], i) => (
            <li key={t} className="flex gap-4 md:flex-col md:items-center md:text-center">
              <span className="num grid h-10 w-10 shrink-0 place-items-center rounded-full bg-navy text-sm font-bold text-white">{i + 1}</span>
              <div>
                <h3 className="font-bold md:mt-1">{t}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">{d}</p>
              </div>
            </li>
          ))}
        </ol>
        <p className="mx-auto mt-10 max-w-2xl rounded-xl bg-white px-4 py-3 text-center text-sm text-muted ring-1 ring-line">
          <b className="text-navy">Official data only.</b> Every cutoff comes from CET Cell PDFs and is checked against them. <Link href="/data" className="font-semibold text-brand-ink underline">How we verify</Link>
        </p>
      </section>

      {/* FAQ */}
      <section className="mx-auto mt-16 max-w-3xl px-4 md:mt-24">
        <h2 className="text-center text-2xl font-bold tracking-tight md:text-3xl">Questions</h2>
        <div className="card mt-6 divide-y divide-line px-4 md:px-6">
          {FAQ.map(([q, a]) => (
            <details key={q} className="group py-4">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold">{q}
                <svg className="shrink-0 text-muted transition group-open:rotate-45" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><path d="M12 5v14M5 12h14" /></svg>
              </summary>
              <p className="mt-2 text-sm leading-relaxed text-muted md:text-[15px]">{a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* CLOSING CTA */}
      <section className="mx-auto mt-16 max-w-6xl px-4 md:mt-24">
        <div className="flex flex-col items-center gap-4 rounded-2xl bg-navy px-6 py-10 text-center text-white md:py-14">
          <h2 className="text-2xl font-bold tracking-tight md:text-3xl">Ready to see your options?</h2>
          <p className="max-w-md text-sm text-white/65 md:text-base">It takes 10 seconds. No sign-up.</p>
          <Link href="/predictor" className="mt-2 rounded-xl bg-brand px-7 py-3.5 font-bold text-navy transition hover:brightness-95">Find my college →</Link>
        </div>
      </section>
    </main>
  );
}
