"use client";
import { Fragment, useEffect, useRef, useState } from "react";
import { API, CAT_GROUPS, Meta, PredictItem, PredictResponse, SEAT_SHORT, catInfo, catLabel } from "@/lib/api";

const GROUP_HINT: Record<string, string> = { General: "General (anyone)", Ladies: "Ladies (girls only)", Other: "EWS / TFWS / other", Defence: "Defence", PwD: "Persons with disability" };
import { DataBanner } from "./Chrome";

type Tone = "green" | "amber" | "red" | "navy";
const STATUS: Record<string, { label: string; tone: Tone; bar: string; edge: string; head: string; blurb: string }> = {
  safer_historical: { label: "Safer", tone: "green", bar: "bg-emerald-500", edge: "border-l-emerald-500", head: "Safer historical options", blurb: "Your percentile is above the past closing cutoff." },
  moderate: { label: "Moderate", tone: "amber", bar: "bg-amber-500", edge: "border-l-amber-500", head: "Moderate — close to the cutoff", blurb: "Your percentile is within 1 point of the past closing cutoff." },
  ambitious: { label: "Ambitious", tone: "red", bar: "bg-rose-500", edge: "border-l-rose-500", head: "Ambitious — below the cutoff", blurb: "Your percentile is below the past closing cutoff. Closest reaches are listed first." },
  insufficient_data: { label: "No data", tone: "navy", bar: "bg-navy/30", edge: "border-l-navy/30", head: "Not enough data", blurb: "No official value to compare." },
};
const ORDER = ["safer_historical", "moderate", "ambitious", "insufficient_data"];
const fmtGap = (g: string | null) => (g == null ? "—" : `${Number(g) > 0 ? "+" : ""}${Number(g).toFixed(2)}`);

function Card({ it, sources, preview }: { it: PredictItem; sources: Record<string, string | null>; preview: string[] }) {
  const st = STATUS[it.status] ?? STATUS.insufficient_data;
  const h = it.records[it.headline_idx];
  const cut = h.closing_percentile != null ? Number(h.closing_percentile) : null;
  const gap = h.gap == null ? null : Number(h.gap);
  return (
    <li className={`card border-l-4 p-4 md:p-5 ${st.edge}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <a href={`/colleges/${it.college_slug}`} className="line-clamp-2 font-semibold leading-snug hover:underline md:text-[17px]">{it.college}</a>
          <p className="mt-0.5 line-clamp-2 text-sm text-muted">{it.branch}</p>
        </div>
        <div className="shrink-0 text-right">
          <p className="num text-2xl font-bold leading-none">{cut == null ? "—" : cut.toFixed(2)}</p>
          <p className="mt-1 whitespace-nowrap text-[11px] text-muted">closed · {h.year.slice(0, 4)} R{h.round}</p>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
        {gap != null && (
          <span className={`num rounded-md px-2 py-0.5 font-semibold ${gap >= 0 ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>
            {gap >= 0 ? `${gap.toFixed(2)} above` : `${Math.abs(gap).toFixed(2)} below`}
          </span>
        )}
        <span className="rounded-md bg-navy/[.07] px-2 py-0.5" title={it.category}>{catLabel(it.category)}</span>
        <span className="rounded-md bg-navy/[.07] px-2 py-0.5">{SEAT_SHORT[it.seat_type_code] ?? it.seat_type_code}</span>
      </div>

      <details className="group mt-3 border-t border-line pt-3">
        <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-brand-ink">
          <span>Cutoff history · {it.records.length} record{it.records.length > 1 ? "s" : ""}</span>
          <svg className="transition group-open:rotate-180" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><path d="M6 9l6 6 6-6" /></svg>
        </summary>
        <div className="mt-2">
          <table className="w-full text-left text-xs">
            <thead className="text-navy/50"><tr><th className="py-1 font-medium">Year · round</th><th className="font-medium">Stage</th><th className="font-medium">Closing</th><th className="hidden font-medium sm:table-cell">Rank</th><th className="font-medium">vs you</th><th className="font-medium">Source</th></tr></thead>
            <tbody>
              {it.records.map((r, i) => {
                const rs = STATUS[r.status] ?? STATUS.insufficient_data;
                return (
                  <tr key={i} className="border-t border-line">
                    <td className="whitespace-nowrap py-1.5 pr-2">{r.year.slice(0, 4)} · R{r.round}{preview.includes(`${r.year}|${r.round}`) && <span className="ml-1.5 rounded bg-amber-100 px-1 text-[10px] font-semibold text-amber-900">preview</span>}</td>
                    <td>{r.stage_label}</td>
                    <td className="font-semibold tabular-nums">{r.closing_percentile == null ? "—" : Number(r.closing_percentile).toFixed(2)}</td>
                    <td className="hidden tabular-nums sm:table-cell">{r.closing_rank ?? "—"}</td>
                    <td><span className="inline-flex items-center gap-1.5"><span className={`h-2 w-2 rounded-full ${rs.bar}`} />{fmtGap(r.gap)}</span></td>
                    <td>{sources[`${r.year}|${r.round}`] ? <a className="text-brand-ink hover:underline" href={sources[`${r.year}|${r.round}`]!} target="_blank" rel="noreferrer">PDF p.{r.source_page}</a> : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="mt-2 text-[11px] text-navy/45">Printed as “{h.original_text}” (latest). Extracted from the official PDF and cross-checked.{it.records.some((r) => preview.includes(`${r.year}|${r.round}`)) ? " Rows marked “preview” are awaiting CET Cell confirmation." : ""}</p>
        </div>
      </details>
    </li>
  );
}

export default function Predictor({ meta, initialPct, initialCat }: { meta: Meta; initialPct: string; initialCat: string }) {
  // Only accept a category the State Level list actually has (the URL is user input).
  const okCat = meta.categories.some((c) => c.seat_type_code === "STATE_LEVEL" && c.code === initialCat) ? initialCat : "";
  const [f, setF] = useState({ percentile: initialPct, seat_type: "STATE_LEVEL", category: okCat, year: "", branch: "" });
  const results = useRef<HTMLElement>(null);
  const autoScroll = useRef(false);
  const [res, setRes] = useState<PredictResponse | null>(null);
  const [items, setItems] = useState<PredictItem[]>([]);
  const [you, setYou] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [show, setShow] = useState("");
  const [asked, setAsked] = useState<typeof f | null>(null);   // the inputs the current results were computed for
  const cats = Array.from(new Set(meta.categories.filter((c) => c.seat_type_code === f.seat_type).map((c) => c.code)));
  const seats = meta.seat_types.filter((s) => s.code !== "ALL_INDIA");
  const inp = "field mt-1.5";

  /** Fetch one page (the server returns 30 at a time). `append` adds to the list, otherwise it replaces it. */
  async function load(q: typeof f, status: string, offset: number, append: boolean) {
    setBusy(true); setErr("");
    try {
      const r = await fetch(`${API}/api/v1/predict`, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exam_code: "MHT_CET", percentile: q.percentile, category: q.category, seat_type: q.seat_type,
          year: q.year || null, branch: q.branch, status: status || null, offset }) });
      if (!r.ok) throw new Error((await r.json()).detail ?? r.status);
      const d: PredictResponse = await r.json();
      setRes((prev) => (append && prev ? { ...d, sources: { ...prev.sources, ...d.sources } } : d));
      setItems((prev) => (append ? [...prev, ...d.items] : d.items));
      setYou(Number(q.percentile)); setAsked(q); setShow(status);
    } catch (x) { setErr(`Could not compute results: ${(x as Error).message}`); } finally { setBusy(false); }
  }
  const submit = (e: React.FormEvent) => { e.preventDefault(); load(f, "", 0, false); };

  // Arriving from the home page with percentile + category: show results straight away.
  const pctOk = initialPct !== "" && Number(initialPct) >= 0 && Number(initialPct) <= 100;
  useEffect(() => {
    if (!(pctOk && okCat)) return;
    autoScroll.current = true;
    const t = setTimeout(() => load({ percentile: initialPct, seat_type: "STATE_LEVEL", category: okCat, year: "", branch: "" }, "", 0, false), 0);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => {   // after the first auto-loaded results are on screen, bring them into view
    if (res && autoScroll.current) { autoScroll.current = false; results.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }
  }, [res]);

  return (
    <div className="mt-8">
      <DataBanner meta={meta} />
      <form onSubmit={submit} className="card mt-4 p-4 md:p-6">
        <div className="grid gap-5 sm:grid-cols-2">
          <label className="text-sm font-semibold">1. Your MHT-CET percentile
            <input className={`${inp} num h-12 text-lg`} inputMode="decimal" required type="number" min="0" max="100" step="0.0000001" placeholder="e.g. 92.5" value={f.percentile} onChange={(e) => setF({ ...f, percentile: e.target.value })} /></label>
          <label className="text-sm font-semibold">2. Your category
            <select className={`${inp} h-12`} required value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })}>
              <option value="">Choose your category…</option>
              {CAT_GROUPS.map((g) => {
                const list = cats.filter((c) => catInfo(c).group === g).sort((a, b) => Number(catInfo(b).label === "Open") - Number(catInfo(a).label === "Open"));
                return list.length > 0 && (
                  <optgroup key={g} label={GROUP_HINT[g]}>
                    {list.map((c) => <option key={c} value={c}>{catInfo(c).label} ({c})</option>)}
                  </optgroup>
                );
              })}
            </select>
            <span className="mt-1 block text-xs font-normal text-muted">Girls can check both “General” and “Ladies” seats — try each.</span></label>
          <label className="text-sm font-semibold sm:col-span-2">3. Seat type
            <select className={inp} value={f.seat_type} onChange={(e) => setF({ ...f, seat_type: e.target.value, category: "" })}>
              {seats.map((s) => <option key={s.code} value={s.code}>{SEAT_SHORT[s.code] ?? s.name}</option>)}</select>
            <span className="mt-1 block text-xs font-normal text-muted">Not sure? Keep <b>State Level</b>. Pick a “Home Univ.” option only if the college is in your home university&apos;s region.</span></label>
        </div>

        <details className="group mt-5 border-t border-line pt-4">
          <summary className="cursor-pointer list-none text-sm font-medium text-brand-ink">
            <span className="group-open:hidden">+ Narrow by year or branch (optional)</span><span className="hidden group-open:inline">− Hide extra filters</span>
          </summary>
          <div className="mt-4 grid gap-5 sm:grid-cols-2">
            <label className="text-sm font-medium">Year
              <select className={inp} value={f.year} onChange={(e) => setF({ ...f, year: e.target.value })}>
                <option value="">All years (compare latest)</option>{meta.years.map((y) => <option key={y}>{y}</option>)}</select></label>
            <label className="text-sm font-medium">Branch name contains
              <input className={inp} value={f.branch} placeholder="e.g. Computer" onChange={(e) => setF({ ...f, branch: e.target.value })} /></label>
          </div>
        </details>

        <button disabled={busy} className="mt-6 w-full rounded-xl bg-brand px-8 py-3.5 font-semibold text-navy shadow-lg shadow-brand/25 transition hover:brightness-95 disabled:opacity-60 sm:w-auto">{busy && !res ? "Comparing…" : "Show my colleges →"}</button>
      </form>
      {err && <p role="alert" className="mt-4 text-rose-700">{err}</p>}

      {res && asked && (
        <section ref={results} className="mt-10 scroll-mt-16" aria-live="polite">
          <div className="card flex flex-wrap items-center justify-between gap-x-6 gap-y-2 bg-navy p-4 text-white md:p-5">
            <div>
              <p className="text-xs uppercase tracking-wide text-white/55">Your percentile</p>
              <p className="num text-3xl font-bold text-brand">{you.toFixed(2)}</p>
            </div>
            <p className="text-sm text-white/75">{catLabel(asked.category)} · {SEAT_SHORT[asked.seat_type] ?? asked.seat_type}{asked.year ? ` · ${asked.year}` : ""}</p>
          </div>
          <h2 className="mt-6 text-xl font-bold tracking-tight md:text-2xl">
            {(res.summary.safer_historical + res.summary.moderate + res.summary.ambitious).toLocaleString()} college branches compared
          </h2>
          <p className="mt-1 text-sm text-muted">{res.basis}</p>
          <p className="mt-2 flex gap-2 text-xs text-muted"><span aria-hidden>ⓘ</span>{res.disclaimer}</p>

          <div className="sticky top-14 z-20 -mx-4 mt-4 bg-background/95 px-4 py-2 backdrop-blur md:static md:mx-0 md:bg-transparent md:px-0" role="group" aria-label="Filter results">
            <div className="grid grid-cols-3 gap-1 rounded-xl bg-navy/[.06] p-1">
              {(["safer_historical", "moderate", "ambitious"] as const).map((k) => {
                const on = show === k, st = STATUS[k];
                return (
                  <button key={k} disabled={busy} onClick={() => load(asked, on ? "" : k, 0, false)} aria-pressed={on}
                    className={`rounded-lg px-2 py-2 text-left transition ${on ? "bg-white shadow-sm ring-1 ring-navy/10" : "hover:bg-white/60"}`}>
                    <span className="flex items-center gap-1.5 text-[11px] font-medium text-muted md:text-xs"><span className={`h-2 w-2 shrink-0 rounded-full ${st.bar}`} /><span className="truncate">{st.label}</span></span>
                    <span className="num mt-0.5 block text-xl font-bold">{res.summary[k]}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {res.total === 0 && <p className="mt-8 rounded-xl bg-white p-6 text-center">No official records match this category, seat type and year. We don&apos;t estimate missing data.</p>}

          <ul className="mt-3 grid gap-3 lg:grid-cols-2">
            {items.map((it, i) => {
              const first = i === 0 || items[i - 1].status !== it.status;
              const st = STATUS[it.status] ?? STATUS.insufficient_data;
              return (
                <Fragment key={`${it.college_slug}-${it.choice_code}-${it.seat_type_code}`}>
                  {first && !show && (
                    <li className="pt-3 lg:col-span-2">
                      <h3 className="flex items-center gap-2 text-sm font-bold"><span className={`h-2 w-2 rounded-full ${st.bar}`} />{st.head}</h3>
                      <p className="mt-0.5 text-xs text-muted">{st.blurb}</p>
                    </li>
                  )}
                  <Card it={it} sources={res.sources} preview={meta.preview_rounds ?? []} />
                </Fragment>
              );
            })}
          </ul>
          {items.length < res.total && (
            <div className="mt-6 text-center">
              <button disabled={busy} onClick={() => load(asked, show, items.length, true)} className="rounded-xl border border-navy/20 bg-white px-6 py-3 font-medium hover:bg-navy/5 disabled:opacity-60">
                {busy ? "Loading…" : "Show 30 more"} <span className="text-navy/50">({items.length} of {res.total})</span></button>
            </div>)}
        </section>
      )}
    </div>
  );
}
