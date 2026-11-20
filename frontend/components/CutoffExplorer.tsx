"use client";
import { useEffect, useState } from "react";
import { API, Cutoff, Meta, SEAT_SHORT, catLabel, pct } from "@/lib/api";
import { DataBanner } from "./Chrome";

type Res = { total: number; page: number; page_size: number; items: Cutoff[] };

export default function CutoffExplorer({ meta, initial }: { meta: Meta; initial: { college?: string; branch?: string } }) {
  const [f, setF] = useState({ branch: initial.branch ?? "", category: "", seat_type: "", year: "", round: "", page: 1 });
  const [res, setRes] = useState<Res | null>(null);
  const [err, setErr] = useState("");
  const set = (k: string, v: string) => setF((s) => ({ ...s, [k]: v, page: 1 }));

  useEffect(() => {
    const qs = new URLSearchParams({ page: String(f.page) });
    if (initial.college) qs.set("college_slug", initial.college);
    (["branch", "category", "seat_type", "year", "round"] as const).forEach((k) => f[k] && qs.set(k, f[k]));
    const t = setTimeout(() => {
      fetch(`${API}/api/v1/cutoffs?${qs}`).then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((d) => { setRes(d); setErr(""); }).catch(() => setErr("Could not load cutoffs. Please try again in a moment."));
    }, 250);
    return () => clearTimeout(t);
  }, [f, initial.college]);

  const cats = Array.from(new Set(meta.categories.filter((c) => !f.seat_type || c.seat_type_code === f.seat_type).map((c) => c.code)));
  const sel = "rounded-xl border border-navy/15 bg-white px-3 py-2 text-sm outline-none focus:border-brand focus:ring-4 focus:ring-brand/15";
  const pages = res ? Math.ceil(res.total / res.page_size) : 0;

  return (
    <div className="mt-8">
      <DataBanner meta={meta} />
      {initial.college && <p className="mt-3 text-sm">Showing one college. <a className="font-semibold text-brand-ink" href="/cutoffs">Clear</a></p>}
      <div className="mt-4 grid gap-3 rounded-2xl border border-line bg-white p-4 shadow-[var(--shadow-card)] sm:grid-cols-2 lg:grid-cols-5">
        <label className="text-sm">Branch<input className={`${sel} mt-1 w-full`} value={f.branch} onChange={(e) => set("branch", e.target.value)} placeholder="e.g. Computer" /></label>
        <label className="text-sm">Seat type<select className={`${sel} mt-1 w-full`} value={f.seat_type} onChange={(e) => set("seat_type", e.target.value)}>
          <option value="">All</option>{meta.seat_types.filter((s) => s.code !== "ALL_INDIA").map((s) => <option key={s.code} value={s.code}>{SEAT_SHORT[s.code] ?? s.name}</option>)}</select></label>
        <label className="text-sm">Category<select className={`${sel} mt-1 w-full`} value={f.category} onChange={(e) => set("category", e.target.value)}>
          <option value="">All</option>{cats.map((c) => <option key={c} value={c}>{catLabel(c)} ({c})</option>)}</select></label>
        <label className="text-sm">Year<select className={`${sel} mt-1 w-full`} value={f.year} onChange={(e) => set("year", e.target.value)}>
          <option value="">All</option>{meta.years.map((y) => <option key={y}>{y}</option>)}</select></label>
        <label className="text-sm">CAP round<select className={`${sel} mt-1 w-full`} value={f.round} onChange={(e) => set("round", e.target.value)}>
          <option value="">All</option>{meta.rounds.map((r) => <option key={r} value={r}>Round {r}</option>)}</select></label>
      </div>

      {err && <p role="alert" className="mt-4 text-rose-700">{err}</p>}
      <p className="mt-4 text-sm text-navy/70" aria-live="polite">{res ? `${res.total.toLocaleString()} records` : "Loading…"}</p>
      <div className="mt-2 max-h-[70vh] overflow-auto rounded-2xl border border-line bg-white shadow-[var(--shadow-card)]">
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="sticky top-0 z-10 bg-[#ebebe0] text-xs uppercase tracking-wide text-navy/70"><tr>
            {["College", "Branch", "Year / Round", "Category", "Seat type", "Closing percentile", "Rank", "Source"].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}
          </tr></thead>
          <tbody className="divide-y divide-navy/5">
            {res?.items.map((r, i) => (
              <tr key={i} className="even:bg-navy/[.015] hover:bg-brand/5">
                <td className="px-3 py-2"><a className="font-medium hover:underline" href={`/colleges/${r.college_slug}`}>{r.college}</a></td>
                <td className="px-3 py-2">{r.branch}</td>
                <td className="px-3 py-2 whitespace-nowrap">{r.year} · R{r.round}{r.verification_status === "pending" && <span className="ml-1.5 rounded bg-amber-100 px-1 text-[10px] font-semibold text-amber-900">preview</span>}{` · stage ${r.stage_label}`}</td>
                <td className="px-3 py-2"><span className="whitespace-nowrap rounded-md bg-navy/8 px-1.5 py-0.5 text-xs" title={r.category}>{catLabel(r.category)}</span></td>
                <td className="px-3 py-2 text-xs" title={r.seat_type}>{SEAT_SHORT[r.seat_type_code] ?? r.seat_type}</td>
                <td className="px-3 py-2 font-semibold tabular-nums text-navy">{pct(r.closing_percentile)}</td>
                <td className="px-3 py-2 tabular-nums">{r.closing_rank ?? "—"}</td>
                <td className="px-3 py-2 whitespace-nowrap">{r.source_url ? <a className="text-brand-ink hover:underline" href={r.source_url} target="_blank" rel="noreferrer">PDF p.{r.source_page}</a> : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm">
          <button disabled={f.page <= 1} onClick={() => setF((s) => ({ ...s, page: s.page - 1 }))} className="rounded-xl border border-navy/20 bg-white px-5 py-2.5 font-medium disabled:opacity-40">← Previous</button>
          <span>Page {f.page} of {pages.toLocaleString()}</span>
          <button disabled={f.page >= pages} onClick={() => setF((s) => ({ ...s, page: s.page + 1 }))} className="rounded-xl border border-navy/20 bg-white px-5 py-2.5 font-medium disabled:opacity-40">Next →</button>
        </div>
      )}
    </div>
  );
}
