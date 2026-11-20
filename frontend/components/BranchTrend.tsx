"use client";
import Link from "next/link";
import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { API, pct } from "@/lib/api";

type Opt = { seat_type_code: string; seat_type: string; category: string; years: number };
type Pt = { year: string; round: number; stage_label: string; closing_percentile: string | null; closing_rank: number | null; original_text: string; source_url: string | null; source_page: number | null; verification_status: string };

export default function BranchBlock({ slug, code, href, hasTrend, left, intake }: { slug: string; code: string; href: string; hasTrend: boolean; left: React.ReactNode; intake: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [opts, setOpts] = useState<Opt[]>([]);
  const [sel, setSel] = useState<{ seat: string; cat: string }>({ seat: "", cat: "" });
  const [pts, setPts] = useState<Pt[] | null>(null);
  const [err, setErr] = useState("");

  async function load(seat: string, cat: string) {
    setSel({ seat, cat }); setPts(null);
    try {
      const r = await fetch(`${API}/api/v1/trends?${new URLSearchParams({ college_slug: slug, choice_code: code, category: cat, seat_type: seat })}`);
      if (!r.ok) throw new Error(String(r.status));
      setPts((await r.json()).points);
    } catch { setErr("Could not load the trend."); }
  }
  async function toggle() {
    const next = !open; setOpen(next);
    if (next && opts.length === 0) {
      try {
        const r = await fetch(`${API}/api/v1/trend-options?${new URLSearchParams({ college_slug: slug, choice_code: code })}`);
        const o: Opt[] = (await r.json()).options; setOpts(o);
        const d = o.find((x) => x.seat_type_code === "STATE_LEVEL" && x.category === "GOPENS") ?? o[0];
        if (d) load(d.seat_type_code, d.category);
      } catch { setErr("Could not load options."); }
    }
  }
  const seats = Array.from(new Map(opts.map((o) => [o.seat_type_code, o.seat_type])).entries());
  const cats = opts.filter((o) => o.seat_type_code === sel.seat).map((o) => o.category);
  const data = (pts ?? []).filter((p) => p.closing_percentile != null).map((p) => ({ label: `${p.year} R${p.round}`, pct: Number(p.closing_percentile), p }));
  const s = "rounded-lg border border-navy/15 bg-white px-2.5 py-1.5 text-sm";

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        {left}
        <div className="flex flex-wrap items-start gap-2">
          {hasTrend && (
            <button onClick={toggle} aria-expanded={open} className="rounded-lg border border-brand/30 px-3.5 py-1.5 text-sm font-semibold text-brand-ink transition hover:bg-brand hover:text-navy">
              {open ? "Hide trend" : "Cutoff trend"}
            </button>
          )}
          <Link href={href} className="rounded-lg border border-navy/20 px-3.5 py-1.5 text-sm font-semibold transition hover:bg-navy hover:text-white">All cutoffs →</Link>
        </div>
      </div>
      {intake}
      {open && (
        <div className="mt-3 w-full rounded-xl bg-navy/[.03] p-4">
          {err && <p role="alert" className="text-sm text-rose-700">{err}</p>}
          {opts.length === 0 && !err && <p className="text-sm text-navy/60">Loading…</p>}
          {opts.length > 0 && (
            <div className="flex flex-wrap gap-3 text-sm">
              <label>Seat type <select className={s} value={sel.seat} onChange={(e) => load(e.target.value, opts.find((o) => o.seat_type_code === e.target.value)!.category)}>
                {seats.map(([c, n]) => <option key={c} value={c}>{n}</option>)}</select></label>
              <label>Category <select className={s} value={sel.cat} onChange={(e) => load(sel.seat, e.target.value)}>
                {cats.map((c) => <option key={c}>{c}</option>)}</select></label>
            </div>
          )}
          {pts && data.length === 0 && <p className="mt-3 text-sm">Data not available for this selection.</p>}
          {data.length > 0 && (
            <>
              <div className="mt-4 h-56 w-full" role="img" aria-label={`Closing percentile by round for ${sel.cat}`}>
                <ResponsiveContainer>
                  <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
                    <CartesianGrid stroke="#1c1c1c" strokeOpacity={0.08} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} width={40} />
                    <Tooltip formatter={(v) => [Number(v).toFixed(4), "Closing percentile"]} />
                    <Line type="monotone" dataKey="pct" stroke="#ff6600" strokeWidth={2.5} dot={{ r: 4 }} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <table className="mt-3 w-full text-left text-xs">
                <thead className="text-navy/55"><tr><th className="py-1">Year · round</th><th>Stage</th><th>Closing percentile</th><th>Rank</th><th>Source</th></tr></thead>
                <tbody>
                  {(pts ?? []).map((p, i) => (
                    <tr key={i} className="border-t border-line">
                      <td className="py-1.5">{p.year} · R{p.round}</td><td>{p.stage_label}</td>
                      <td className="font-semibold tabular-nums">{pct(p.closing_percentile)}</td><td className="tabular-nums">{p.closing_rank ?? "—"}</td>
                      <td>{p.source_url ? <a className="text-brand-ink hover:underline" href={p.source_url} target="_blank" rel="noreferrer">PDF p.{p.source_page}</a> : "—"}</td>
                    </tr>))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}
    </div>
  );
}
