import Link from "next/link";
import { Logo } from "./Logo";

const NAV = [["Colleges", "/colleges"], ["Cutoff explorer", "/cutoffs"], ["College predictor", "/predictor"], ["How we verify data", "/data"]];

export function Footer() {
  return (
    <footer className="mt-28 bg-navy text-white">
      <div className="mx-auto max-w-6xl px-4 pb-10 pt-16">
        <div className="grid gap-12 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <Logo onDark size={46} />
            <p className="mt-5 max-w-sm text-[15px] leading-relaxed text-white/65">
              Real CAP cutoffs from the Maharashtra CET Cell, in one place. Independent — not affiliated with the CET Cell, DMER or MCC.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">Explore</p>
            <ul className="mt-4 space-y-2.5 text-[15px]">{NAV.map(([l, h]) => <li key={h}><Link href={h} className="text-white/85 hover:text-brand">{l}</Link></li>)}</ul>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">Official sources</p>
            <ul className="mt-4 space-y-2.5 text-[15px]">
              <li><a className="text-white/85 hover:text-brand" href="https://cetcell.mahacet.org/" target="_blank" rel="noreferrer">Maharashtra CET Cell ↗</a></li>
              <li><a className="text-white/85 hover:text-brand" href="https://fe2025.mahacet.org/" target="_blank" rel="noreferrer">FE CAP portal ↗</a></li>
            </ul>
          </div>
        </div>
        <p className="mt-14 border-t border-white/10 pt-6 text-xs leading-relaxed text-white/50">
          Historical cutoffs do not guarantee future admission. Always confirm on the official CAP portal. Data shown is machine-extracted from published CET Cell PDFs and may be marked as preview until verified.
        </p>
      </div>
    </footer>
  );
}

export function DataBanner({ meta }: { meta: { preview_rounds?: string[] } }) {
  const preview = (meta.preview_rounds ?? []).map((k) => { const [y, r] = k.split("|"); return `${y} Round ${r}`; });
  if (preview.length) {
    return (
      <p role="note" className="flex items-center gap-2 text-xs text-muted">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" aria-hidden />
        <span><b className="text-navy">{preview.join(", ")}</b> is marked “preview” (awaiting CET Cell confirmation). All other data is cross-checked with official PDFs. <a className="font-semibold text-brand-ink underline" href="/data">How we verify</a></span>
      </p>
    );
  }
  return (
    <p role="note" className="flex items-center gap-2 text-xs text-muted">
      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" aria-hidden />
      <span>Cross-checked against official CET Cell PDFs. <a className="font-semibold text-emerald-800 underline" href="/data">How we verify</a></span>
    </p>
  );
}

export function Pill({ children, tone = "navy" }: { children: React.ReactNode; tone?: "navy" | "green" | "amber" | "red" | "light" }) {
  const t = { navy: "bg-navy/[.07] text-navy", green: "bg-emerald-100 text-emerald-800", amber: "bg-amber-100 text-amber-900", red: "bg-rose-100 text-rose-800", light: "bg-white/15 text-white ring-1 ring-white/25" }[tone];
  return <span className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${t}`}>{children}</span>;
}

/** Light, editorial page header: orange rule, large title, muted lede. */
export function PageHeader({ title, children, crumb, eyebrow }: { title: string; children?: React.ReactNode; crumb?: React.ReactNode; eyebrow?: string }) {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-6xl px-4 pb-6 pt-8 md:pb-8 md:pt-10">
        {crumb && <div className="mb-4 text-sm text-muted">{crumb}</div>}
        {eyebrow && <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-brand-ink">{eyebrow}</p>}
        <h1 className="rise max-w-4xl text-3xl font-bold leading-tight tracking-tight md:text-4xl">{title}</h1>
        <span className="mt-3 block h-1 w-10 rounded bg-brand" aria-hidden />
        {children && <div className="rise rise-2 mt-3 max-w-2xl text-base leading-relaxed text-muted">{children}</div>}
      </div>
    </section>
  );
}
