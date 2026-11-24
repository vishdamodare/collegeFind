"use client";
import { useEffect, useRef, useState } from "react";
import { API, Cutoff, Meta, SEAT_SHORT, catLabel, pct } from "@/lib/api";
import { DataBanner } from "./Chrome";

type Res = { total: number; page: number; page_size: number; items: Cutoff[] };
type F = { branch: string; category: string; seat_type: string; year: string; round: string; page: number };
const KEYS = ["seat_type", "category", "year", "round"] as const;

function Source({ r }: { r: Cutoff }) {
  return r.source_url
    ? <a className="whitespace-nowrap text-brand-ink underline-offset-2 hover:underline" href={r.source_url} target="_blank" rel="noreferrer">PDF p.{r.source_page}</a>
    : <span className="text-muted">—</span>;
}
const Preview = ({ r }: { r: Cutoff }) =>
  r.verification_status === "pending" ? <span className="ml-1.5 rounded bg-amber-100 px-1 text-[10px] font-semibold text-amber-900">preview</span> : null;

export default function CutoffExplorer({ meta, initial }: { meta: Meta; initial: { college?: string; branch?: string } }) {
  const [f, setF] = useState<F>({ branch: initial.branch ?? "", category: "", seat_type: "", year: "", round: "", page: 1 });
  const [loaded, setLoaded] = useState<{ key: string; res?: Res; err?: string } | null>(null);
  const [sheet, setSheet] = useState(false);
  const top = useRef<HTMLDivElement>(null);
  const set = (k: keyof F, v: string) => setF((s) => ({ ...s, [k]: v, page: 1 }));

  const qs = new URLSearchParams({ page: String(f.page) });
  if (initial.college) qs.set("college_slug", initial.college);
  (["branch", ...KEYS] as const).forEach((k) => f[k] && qs.set(k, f[k]));
  const key = qs.toString();

  useEffect(() => {
    const ctl = new AbortController();   // a newer filter/page always wins: older responses are cancelled
    const t = setTimeout(() => {
      fetch(`${API}/api/v1/cutoffs?${key}`, { signal: ctl.signal })
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((d: Res) => setLoaded({ key, res: d }))
        .catch((e) => { if (e?.name !== "AbortError") setLoaded((p) => ({ key, res: p?.res, err: "Could not load cutoffs. Please try again in a moment." })); });
    }, 250);
    return () => { clearTimeout(t); ctl.abort(); };
  }, [key]);
  const res = loaded?.res ?? null;
  const err = loaded?.key === key ? loaded.err ?? "" : "";
  const busy = loaded?.key !== key;

  const go = (page: number) => { setF((s) => ({ ...s, page })); top.current?.scrollIntoView({ behavior: "smooth", block: "start" }); };
  const cats = Array.from(new Set(meta.categories.filter((c) => !f.seat_type || c.seat_type_code === f.seat_type).map((c) => c.code)));
  const pages = res ? Math.ceil(res.total / res.page_size) : 0;
  const label: Record<(typeof KEYS)[number], (v: string) => string> = {
    seat_type: (v) => SEAT_SHORT[v] ?? v, category: (v) => `${catLabel(v)} (${v})`, year: (v) => v, round: (v) => `Round ${v}`,
  };
  const active = KEYS.filter((k) => f[k]);

  const selects = (
    <>
      <label className="block"><span className="label">Seat type</span>
        <select className="field" value={f.seat_type} onChange={(e) => setF((s) => ({ ...s, seat_type: e.target.value, category: "", page: 1 }))}>
          <option value="">All seat types</option>
          {meta.seat_types.filter((s) => s.code !== "ALL_INDIA").map((s) => <option key={s.code} value={s.code}>{SEAT_SHORT[s.code] ?? s.name}</option>)}
        </select></label>
      <label className="block"><span className="label">Category</span>
        <select className="field" value={f.category} onChange={(e) => set("category", e.target.value)}>
          <option value="">All categories</option>{cats.map((c) => <option key={c} value={c}>{catLabel(c)} ({c})</option>)}
        </select></label>
      <label className="block"><span className="label">Year</span>
        <select className="field" value={f.year} onChange={(e) => set("year", e.target.value)}>
          <option value="">All years</option>{meta.years.map((y) => <option key={y}>{y}</option>)}
        </select></label>
      <label className="block"><span className="label">CAP round</span>
        <select className="field" value={f.round} onChange={(e) => set("round", e.target.value)}>
          <option value="">All rounds</option>{meta.rounds.map((r) => <option key={r} value={r}>Round {r}</option>)}
        </select></label>
    </>
  );

  return (
    <div className="mt-5 md:mt-8">
      <DataBanner meta={meta} />
      {initial.college && res?.items[0] && (
        <p className="mt-4 flex flex-wrap items-center gap-x-2 text-sm">
          <span className="text-muted">College:</span><b className="min-w-0">{res.items[0].college}</b>
          <a className="font-semibold text-brand-ink underline" href="/cutoffs">Show all colleges</a>
        </p>
      )}

      {/* Filters: one row on desktop; search + sheet on mobile */}
      <div className="mt-4 flex gap-2 md:grid md:grid-cols-[1.3fr_repeat(4,1fr)] md:gap-3 md:rounded-2xl md:border md:border-line md:bg-white md:p-4">
        <label className="block min-w-0 flex-1"><span className="label sr-only md:not-sr-only md:mb-1.5">Branch</span>
          <span className="relative block">
            <svg className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
            <input className="field pl-10" type="search" value={f.branch} onChange={(e) => set("branch", e.target.value)} placeholder="Branch, e.g. Computer" aria-label="Branch" />
          </span>
        </label>
        <button type="button" onClick={() => setSheet(true)} className="flex h-11 shrink-0 items-center gap-2 rounded-xl border border-navy/15 bg-white px-4 font-semibold md:hidden" aria-haspopup="dialog">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><path d="M4 6h16M7 12h10M10 18h4" /></svg>
          Filters{active.length > 0 && <span className="grid h-5 min-w-5 place-items-center rounded-full bg-brand px-1 text-xs text-navy">{active.length}</span>}
        </button>
        <div className="hidden md:contents">{selects}</div>
      </div>

      {active.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 md:hidden">
          {active.map((k) => (
            <button key={k} onClick={() => set(k, "")} className="inline-flex items-center gap-1.5 rounded-full bg-navy px-3 py-1.5 text-xs font-medium text-white" aria-label={`Remove filter ${label[k](f[k])}`}>
              {label[k](f[k])}<span aria-hidden className="text-white/60">✕</span>
            </button>
          ))}
        </div>
      )}

      {sheet && (
        <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true" aria-label="Filters">
          <button className="absolute inset-0 bg-navy/40" aria-label="Close filters" onClick={() => setSheet(false)} />
          <div className="absolute inset-x-0 bottom-0 max-h-[85dvh] overflow-y-auto rounded-t-3xl bg-background px-4 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-3">
            <span className="mx-auto mb-3 block h-1 w-10 rounded-full bg-navy/20" aria-hidden />
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">Filters</h2>
              {active.length > 0 && <button className="text-sm font-semibold text-brand-ink" onClick={() => setF((s) => ({ ...s, seat_type: "", category: "", year: "", round: "", page: 1 }))}>Clear all</button>}
            </div>
            <div className="mt-4 space-y-4">{selects}</div>
            <button onClick={() => setSheet(false)} className="mt-6 h-12 w-full rounded-xl bg-navy font-semibold text-white">
              {busy ? "Updating…" : `Show ${res?.total.toLocaleString() ?? ""} results`}
            </button>
          </div>
        </div>
      )}

      <div ref={top} className="scroll-mt-20" />
      {err && <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{err}</p>}
      <p className="mt-4 text-sm text-muted" aria-live="polite">
        {res ? <><b className="text-navy">{res.total.toLocaleString()}</b> cutoffs{pages > 1 && ` · page ${f.page} of ${pages.toLocaleString()}`}</> : "Loading…"}
      </p>

      <div className={`transition-opacity ${busy && res ? "opacity-50" : ""}`}>
        {res && res.items.length === 0 && (
          <div className="card mt-3 p-8 text-center"><p className="font-semibold">No cutoffs match these filters.</p><p className="mt-1 text-sm text-muted">Try removing a filter or a shorter branch name.</p></div>
        )}

        {/* Mobile: cards */}
        <ul className="mt-3 space-y-3 md:hidden">
          {res?.items.map((r, i) => (
            <li key={`${r.choice_code}-${r.seat_type_code}-${r.category}-${r.year}-${r.round}-${r.stage_label}-${i}`} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <a className="line-clamp-2 font-semibold leading-snug" href={`/colleges/${r.college_slug}`}>{r.college}</a>
                  <p className="mt-0.5 line-clamp-2 text-sm text-muted">{r.branch}</p>
                </div>
                <div className="shrink-0 text-right">
                  <p className="num text-xl font-bold leading-none">{r.closing_percentile == null ? "—" : Number(r.closing_percentile).toFixed(2)}</p>
                  <p className="mt-1 text-[11px] text-muted">{r.closing_percentile == null ? "no percentile" : "percentile"}</p>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
                <span className="rounded-md bg-navy/[.07] px-2 py-0.5 font-medium" title={r.category}>{catLabel(r.category)}</span>
                <span className="rounded-md bg-navy/[.07] px-2 py-0.5">{SEAT_SHORT[r.seat_type_code] ?? r.seat_type}</span>
              </div>
              <div className="mt-3 flex items-center justify-between border-t border-line pt-3 text-xs text-muted">
                <span>{r.year} · Round {r.round} · stage {r.stage_label}<Preview r={r} /></span>
                <span className="flex items-center gap-3"><span className="num">Rank {r.closing_rank ?? "—"}</span><Source r={r} /></span>
              </div>
            </li>
          ))}
        </ul>

        {/* Desktop: table */}
        {res && res.items.length > 0 && (
          <div className="card mt-3 hidden overflow-hidden md:block">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line bg-navy/[.03] text-xs text-muted">
                <tr>{["College / branch", "Year · round", "Category", "Seat type", "Percentile", "Rank", "Source"].map((h, i) => (
                  <th key={h} className={`px-4 py-3 font-semibold ${i === 4 || i === 5 ? "text-right" : ""}`}>{h}</th>))}</tr>
              </thead>
              <tbody className="divide-y divide-line">
                {res.items.map((r, i) => (
                  <tr key={`${r.choice_code}-${r.seat_type_code}-${r.category}-${r.year}-${r.round}-${r.stage_label}-${i}`} className="align-top hover:bg-brand/[.04]">
                    <td className="max-w-[340px] px-4 py-3">
                      <a className="font-medium leading-snug hover:underline" href={`/colleges/${r.college_slug}`}>{r.college}</a>
                      <p className="mt-0.5 text-xs text-muted">{r.branch}</p>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">{r.year} · R{r.round}<Preview r={r} /><p className="text-xs text-muted">stage {r.stage_label}</p></td>
                    <td className="px-4 py-3"><span className="whitespace-nowrap rounded-md bg-navy/[.07] px-1.5 py-0.5 text-xs" title={r.category}>{catLabel(r.category)}</span></td>
                    <td className="px-4 py-3 text-xs text-muted" title={r.seat_type}>{SEAT_SHORT[r.seat_type_code] ?? r.seat_type}</td>
                    <td className="num px-4 py-3 text-right font-semibold">{pct(r.closing_percentile)}</td>
                    <td className="num px-4 py-3 text-right">{r.closing_rank ?? "—"}</td>
                    <td className="px-4 py-3"><Source r={r} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {pages > 1 && (
        <nav aria-label="Pagination" className="mt-5 flex items-center justify-between gap-3 text-sm">
          <button disabled={f.page <= 1 || busy} onClick={() => go(f.page - 1)} className="h-11 rounded-xl border border-navy/20 bg-white px-4 font-medium disabled:opacity-40">← Prev</button>
          <span className="text-muted">Page <b className="text-navy">{f.page}</b> of {pages.toLocaleString()}</span>
          <button disabled={f.page >= pages || busy} onClick={() => go(f.page + 1)} className="h-11 rounded-xl border border-navy/20 bg-white px-4 font-medium disabled:opacity-40">Next →</button>
        </nav>
      )}
    </div>
  );
}
