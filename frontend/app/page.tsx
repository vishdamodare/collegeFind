import Link from "next/link";
import { get, Meta } from "@/lib/api";

const FAQ = [
  ["Does this predict my admission?", "No. It compares your score with what seats closed at in earlier CAP rounds. Cutoffs change every year, so nothing here is a guarantee."],
  ["Where does the data come from?", "Straight from cutoff lists and seat matrices published by the Maharashtra State CET Cell. Every record links back to its source PDF and page."],
  ["Why do some values say “Data not available”?", "We never estimate or fill gaps. If an official value is missing, we say so."],
  ["Is the data verified?", "Imports are machine-extracted and labelled as preview until an admin verifies them. A banner tells you when that applies."],
];

async function stats() {
  try {
    const [m, c] = await Promise.all([get<Meta>("/api/v1/meta"), get<{ total: number }>("/api/v1/colleges?page_size=1")]);
    return { colleges: c.total, records: Object.values(m.records).reduce((a, b) => a + b, 0), years: m.years, rounds: m.rounds.length };
  } catch { return null; }
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mx-auto mt-24 max-w-6xl px-4">
      <div className="border-t-2 border-navy pt-4">
        <h2 className="text-2xl font-bold tracking-tight md:text-3xl">{title}</h2>
      </div>
      <div className="mt-8">{children}</div>
    </section>
  );
}

export default async function Home() {
  const s = await stats();
  return (
    <main>
      {/* HERO */}
      <section className="border-b border-line">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-16 pt-14 md:grid-cols-[1.25fr_1fr] md:pb-24 md:pt-20">
          <div>
            <p className="rise inline-flex items-center gap-2 rounded-full border border-line bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" /> Maharashtra engineering · CAP cutoffs
            </p>
            <h1 className="rise rise-2 mt-6 text-[44px] font-bold leading-[1.02] tracking-tight md:text-[68px]">
              Find the college your percentile <span className="underline-brand">can reach.</span>
            </h1>
            <p className="rise rise-3 mt-6 max-w-xl text-lg leading-relaxed text-muted">
              Compare your MHT-CET score with real, official closing cutoffs — by college, branch, category and round. Every number links to its source page.
            </p>

            <form action="/predictor" className="rise rise-3 mt-9 max-w-xl">
              <label htmlFor="pct" className="text-sm font-semibold">Your MHT-CET percentile</label>
              <div className="mt-2 flex flex-col gap-3 sm:flex-row">
                <input id="pct" name="percentile" type="number" min="0" max="100" step="0.0000001" required placeholder="e.g. 92.5"
                  className="num h-14 flex-1 rounded-lg border-2 border-navy bg-white px-4 text-xl outline-none transition focus:border-brand focus:ring-4 focus:ring-brand/20" />
                <button className="h-14 rounded-lg bg-brand px-8 text-base font-bold text-navy transition hover:brightness-95">Find my college →</button>
              </div>
              <p className="mt-3 text-sm text-muted">No sign-up. JEE Main and NEET UG are coming later.</p>
            </form>
          </div>

          {/* Live data panel */}
          <aside aria-label="Data coverage" className="rise rise-3 relative overflow-hidden rounded-2xl bg-navy p-7 text-white">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/50">Live in our database</p>
            {s ? (
              <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-7">
                {[[s.colleges.toLocaleString(), "Colleges"], [s.records.toLocaleString(), "Cutoff records"], [s.years.length ? s.years[0].slice(0, 4) + "–" + s.years[s.years.length - 1].slice(5) : "—", "Years covered"], [String(s.rounds), "CAP rounds"]].map(([v, l]) => (
                  <div key={l}>
                    <dd className="num text-[32px] font-bold leading-none text-brand">{v}</dd>
                    <dt className="mt-2 text-[13px] text-white/65">{l}</dt>
                  </div>
                ))}
              </dl>
            ) : <p className="mt-5 text-white/70">Data is loading — please refresh in a moment.</p>}
            <p className="mt-8 border-t border-white/15 pt-4 text-[13px] leading-relaxed text-white/60">
              Extracted from the official CET Cell cutoff PDFs. Each record keeps the value exactly as printed, plus its page.
            </p>
          </aside>
        </div>
      </section>

      <Section title="How it works">
        <ol className="grid gap-x-8 gap-y-8 md:grid-cols-3">
          {[["Enter your score", "Your MHT-CET percentile and your category (Open, OBC, SC…). Not sure about seat type? Keep State Level."],
            ["We compare with history", "Your score is matched against official closing cutoffs from past CAP rounds, across years."],
            ["See the evidence", "Every result shows the exact record, round, seat type and a link to the official PDF page."]].map(([t, d], i) => (
            <li key={t} className="border-t border-line pt-5">
              <span className="num text-4xl font-bold text-brand">{String(i + 1).padStart(2, "0")}</span>
              <h3 className="mt-3 text-lg font-bold">{t}</h3>
              <p className="mt-2 leading-relaxed text-muted">{d}</p>
            </li>
          ))}
        </ol>

        <div className="mt-14">
          <h3 className="text-xl font-bold tracking-tight">How to read your results</h3>
          <p className="mt-1 text-muted">Say a seat closed at <span className="num font-semibold text-navy">90.00</span> in a past round. Here is what you would see:</p>

          <ul className="mt-6 grid gap-4 md:grid-cols-3">
            {[
              { you: "93.00", label: "Safer option", why: "You are above where this seat closed.", tone: "border-t-emerald-500", chip: "bg-emerald-100 text-emerald-800", mark: "✓" },
              { you: "90.50", label: "Close call", why: "You are within 1 point. It could go either way.", tone: "border-t-amber-500", chip: "bg-amber-100 text-amber-900", mark: "≈" },
              { you: "86.00", label: "A reach", why: "You are below where this seat closed.", tone: "border-t-rose-500", chip: "bg-rose-100 text-rose-800", mark: "↑" },
            ].map((x) => (
              <li key={x.label} className={`rounded-xl border border-line border-t-4 bg-white p-5 ${x.tone}`}>
                <span className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-sm font-semibold ${x.chip}`}><span aria-hidden>{x.mark}</span>{x.label}</span>
                <dl className="mt-5 grid grid-cols-2 gap-4">
                  <div><dt className="text-xs text-muted">Seat closed at</dt><dd className="num mt-1 text-2xl font-bold">90.00</dd></div>
                  <div><dt className="text-xs text-muted">You scored</dt><dd className="num mt-1 text-2xl font-bold">{x.you}</dd></div>
                </dl>
                <p className="mt-4 border-t border-line pt-4 text-[15px] leading-snug">{x.why}</p>
              </li>
            ))}
          </ul>

          <p className="mt-5 rounded-lg bg-navy/[.05] px-4 py-3 text-sm text-muted">
            <b className="text-navy">Remember:</b> a safer option is not a promise. Cutoffs change every year — this only shows how your score compares with the past.
          </p>
        </div>
      </Section>

      <Section title="Start exploring">
        <ul className="divide-y divide-line border-y border-line">
          {[["/predictor", "College predictor", "Safer, moderate and ambitious options for your percentile."],
            ["/cutoffs", "Cutoff explorer", "Filter every closing cutoff by branch, category, seat type, year and round."],
            ["/colleges", "Find colleges", "Search every college in the CET Cell lists and see its branches, intake and cutoff trends."]].map(([h, t, d]) => (
            <li key={h}>
              <Link href={h} className="group grid items-center gap-2 py-6 md:grid-cols-[1fr_1.4fr_auto] md:gap-8">
                <span className="text-2xl font-bold tracking-tight transition group-hover:text-brand-ink">{t}</span>
                <span className="text-muted">{d}</span>
                <span className="text-2xl transition group-hover:translate-x-1 group-hover:text-brand-ink" aria-hidden>→</span>
              </Link>
            </li>
          ))}
        </ul>
      </Section>

      <section className="mx-auto mt-24 max-w-6xl px-4">
        <div className="grid gap-10 rounded-2xl bg-navy p-8 text-white md:grid-cols-[1fr_1.3fr] md:p-12">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand">Built to be trusted</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">We show our work.</h2>
          </div>
          <ul className="grid gap-x-8 gap-y-6 sm:grid-cols-2">
            {[["Official sources only", "Extracted from cutoff lists published by the Maharashtra CET Cell."], ["Every row is traceable", "Each cutoff links to its source PDF page and shows the value as printed."], ["No guessing", "Missing data is “Data not available” — never zero, never an estimate."], ["Never a guarantee", "Results are a historical comparison. Cutoffs change every year."]].map(([t, d]) => (
              <li key={t} className="border-t border-white/15 pt-4"><b className="block">{t}</b><span className="mt-1 block text-[15px] leading-relaxed text-white/65">{d}</span></li>
            ))}
          </ul>
        </div>
      </section>

      <Section title="Questions">
        <div className="divide-y divide-line border-y border-line">
          {FAQ.map(([q, a]) => (
            <details key={q} className="group py-5">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-lg font-semibold">{q}
                <svg className="shrink-0 transition group-open:rotate-45" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><path d="M12 5v14M5 12h14" /></svg></summary>
              <p className="mt-3 max-w-3xl leading-relaxed text-muted">{a}</p>
            </details>
          ))}
        </div>
      </Section>
    </main>
  );
}
