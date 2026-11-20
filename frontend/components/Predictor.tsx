"use client";
import { Fragment, useState } from "react";
import { API, CAT_GROUPS, Meta, PredictItem, PredictResponse, SEAT_SHORT, catInfo, catLabel, pct } from "@/lib/api";

const GROUP_HINT: Record<string, string> = { General: "General (anyone)", Ladies: "Ladies (girls only)", Other: "EWS / TFWS / other", Defence: "Defence", PwD: "Persons with disability" };
import { DataBanner, Pill } from "./Chrome";

type Tone = "green" | "amber" | "red" | "navy";
const STATUS: Record<string, { label: string; tone: Tone; bar: string; edge: string; head: string; blurb: string }> = {
  safer_historical: { label: "Safer historical", tone: "green", bar: "bg-emerald-500", edge: "border-l-emerald-500", head: "Safer historical options", blurb: "Your percentile is above the past closing cutoff." },
  moderate: { label: "Moderate", tone: "amber", bar: "bg-amber-500", edge: "border-l-amber-500", head: "Moderate — close to the cutoff", blurb: "Your percentile is within 1 point of the past closing cutoff." },
  ambitious: { label: "Ambitious", tone: "red", bar: "bg-rose-500", edge: "border-l-rose-500", head: "Ambitious — below the cutoff", blurb: "Your percentile is below the past closing cutoff. Closest reaches are listed first." },
  insufficient_data: { label: "No data", tone: "navy", bar: "bg-navy/30", edge: "border-l-navy/30", head: "Not enough data", blurb: "No official value to compare." },
};
const ORDER = ["safer_historical", "moderate", "ambitious", "insufficient_data"];
const fmtGap = (g: string | null) => (g == null ? "—" : `${Number(g) > 0 ? "+" : ""}${Number(g).toFixed(2)}`);

/** 0–100 scale. Orange dot = you, dark tick = past closing cutoff. */
function Bar({ you, cutoff, fill }: { you: number; cutoff: number; fill: string }) {
  const at = (v: number) => `${Math.min(100, Math.max(0, v))}%`;
  const lo = Math.min(you, cutoff), hi = Math.max(you, cutoff);
  return (
    <div className="mt-4" role="img" aria-label={`You ${you.toFixed(2)}, past closing cutoff ${cutoff.toFixed(2)}, on a 0 to 100 percentile scale`}>
      <div className="relative h-1.5 rounded-full bg-navy/10">
        <span className={`absolute top-0 h-1.5 rounded-full opacity-60 ${fill}`} style={{ left: at(lo), width: `${Math.max(0, hi - lo)}%` }} />
        <span className="absolute top-1/2 h-4 w-0.5 -translate-x-1/2 -translate-y-1/2 rounded bg-navy" style={{ left: at(cutoff) }} />
        <span className="absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-brand shadow ring-1 ring-navy/20" style={{ left: at(you) }} />
      </div>
      <div className="mt-1.5 flex justify-between text-[10px] tabular-nums text-navy/40"><span>0</span><span>50</span><span>100</span></div>
    </div>
  );
}

function Stat({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <div>
      <dt className="text-[11px] font-medium uppercase tracking-wide text-navy/50">{label}</dt>
      <dd className={`mt-0.5 tabular-nums ${strong ? "text-xl font-bold" : "text-xl font-semibold text-navy/80"}`}>{value}</dd>
    </div>
  );
}

function Card({ it, you, sources, preview }: { it: PredictItem; you: number; sources: Record<string, string | null>; preview: string[] }) {
  const st = STATUS[it.status] ?? STATUS.insufficient_data;
  const h = it.records[it.headline_idx];
  const cut = h.closing_percentile != null ? Number(h.closing_percentile) : null;
  return (
    <li className={`rise rounded-2xl border border-line border-l-4 bg-white p-5 shadow-[var(--shadow-card)] ${st.edge}`}>
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div className="min-w-0">
          <a href={`/colleges/${it.college_slug}`} className="text-[17px] font-semibold leading-snug hover:underline">{it.college}</a>
          <p className="mt-0.5 text-sm text-navy/70">{it.branch}</p>
        </div>
        <Pill tone={st.tone}>{st.label}</Pill>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-md bg-navy/8 px-2 py-0.5" title={it.category}>{catLabel(it.category)}</span>
        <span className="text-navy/60">{SEAT_SHORT[it.seat_type_code] ?? it.seat_type_code}</span>
      </div>

      <dl className="mt-4 grid grid-cols-3 gap-4 border-t border-line pt-4">
        <Stat label={`Closing · ${h.year} R${h.round}`} value={pct(h.closing_percentile)} strong />
        <Stat label="Your percentile" value={you.toFixed(4)} />
        <Stat label="Difference" value={fmtGap(h.gap)} />
      </dl>
      {cut != null && <Bar you={you} cutoff={cut} fill={st.bar} />}

      <details className="group mt-4 border-t border-line pt-3">
        <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-brand-ink">
          <span>Cutoff history · {it.records.length} record{it.records.length > 1 ? "s" : ""}</span>
          <svg className="transition group-open:rotate-180" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><path d="M6 9l6 6 6-6" /></svg>
        </summary>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[460px] text-left text-xs">
            <thead className="text-navy/50"><tr><th className="py-1 font-medium">Year · round</th><th className="font-medium">Stage</th><th className="font-medium">Closing</th><th className="font-medium">Rank</th><th className="font-medium">vs you</th><th className="font-medium">Source</th></tr></thead>
            <tbody>
              {it.records.map((r, i) => {
                const rs = STATUS[r.status] ?? STATUS.insufficient_data;
                return (
                  <tr key={i} className="border-t border-line">
                    <td className="py-1.5 whitespace-nowrap">{r.year} · R{r.round}{preview.includes(`${r.year}|${r.round}`) && <span className="ml-1.5 rounded bg-amber-100 px-1 text-[10px] font-semibold text-amber-900">preview</span>}</td>
                    <td>{r.stage_label}</td>
                    <td className="font-semibold tabular-nums">{pct(r.closing_percentile)}</td>
                    <td className="tabular-nums">{r.closing_rank ?? "—"}</td>
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

export default function Predictor({ meta, initialPct }: { meta: Meta; initialPct: string }) {
  const [f, setF] = useState({ percentile: initialPct, seat_type: "STATE_LEVEL", category: "", year: "", branch: "" });
  const [res, setRes] = useState<PredictResponse | null>(null);
  const [items, setItems] = useState<PredictItem[]>([]);
  const [you, setYou] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [show, setShow] = useState("");
  const [asked, setAsked] = useState<typeof f | null>(null);   // the inputs the current results were computed for
  const cats = Array.from(new Set(meta.categories.filter((c) => c.seat_type_code === f.seat_type).map((c) => c.code)));
  const seats = meta.seat_types.filter((s) => s.code !== "ALL_INDIA");
  const inp = "mt-1.5 w-full rounded-xl border border-navy/15 bg-white px-3.5 py-2.5 outline-none focus:border-brand focus:ring-4 focus:ring-brand/15";

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

  return (
    <div className="mt-8">
      <DataBanner meta={meta} />
      <form onSubmit={submit} className="mt-4 rounded-2xl border border-line bg-white p-6 shadow-[var(--shadow-card)]">
        <div className="grid gap-5 sm:grid-cols-2">
          <label className="text-sm font-semibold">1. Your MHT-CET percentile
            <input className={`${inp} num h-12 text-lg`} required type="number" min="0" max="100" step="0.0000001" placeholder="e.g. 92.5" value={f.percentile} onChange={(e) => setF({ ...f, percentile: e.target.value })} /></label>
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
        <section className="mt-10" aria-live="polite">
          <h2 className="text-2xl font-bold tracking-tight">
            {(res.summary.safer_historical + res.summary.moderate + res.summary.ambitious).toLocaleString()} college branches compared
          </h2>
          <p className="mt-1 text-sm text-navy/60">{res.basis} Every record is listed under “Cutoff history”.</p>
          <p className="mt-3 flex gap-2 text-xs text-navy/60"><span aria-hidden>ⓘ</span>{res.disclaimer}</p>

          <div className="mt-5 grid grid-cols-3 gap-3" role="group" aria-label="Filter results">
            {(["safer_historical", "moderate", "ambitious"] as const).map((k) => {
              const on = show === k, st = STATUS[k];
              return (
                <button key={k} disabled={busy} onClick={() => load(asked, on ? "" : k, 0, false)} aria-pressed={on}
                  className={`rounded-xl border p-3 text-left transition ${on ? "border-navy bg-navy text-white" : "border-line bg-white hover:border-navy/40"}`}>
                  <span className="flex items-center gap-2 text-xs font-medium"><span className={`h-2 w-2 rounded-full ${st.bar}`} />{st.label}</span>
                  <span className="mt-1 block text-2xl font-bold tabular-nums">{res.summary[k]}</span>
                </button>
              );
            })}
          </div>

          {res.total === 0 && <p className="mt-8 rounded-xl bg-white p-6 text-center">No official records match this category, seat type and year. We don&apos;t estimate missing data.</p>}

          <ul className="mt-6 space-y-3">
            {items.map((it, i) => {
              const first = i === 0 || items[i - 1].status !== it.status;
              const st = STATUS[it.status] ?? STATUS.insufficient_data;
              return (
                <Fragment key={`${it.college_slug}-${it.choice_code}-${it.seat_type_code}`}>
                  {first && !show && (
                    <li className="pt-4">
                      <h3 className="text-sm font-semibold uppercase tracking-wide text-navy/60">{st.head}</h3>
                      <p className="text-xs text-navy/50">{st.blurb}</p>
                    </li>
                  )}
                  <Card it={it} you={you} sources={res.sources} preview={meta.preview_rounds ?? []} />
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
