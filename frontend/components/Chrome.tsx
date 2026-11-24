import Link from "next/link";
import { Logo } from "./Logo";

const NAV = [["Colleges", "/colleges"], ["Cutoff explorer", "/cutoffs"], ["College predictor", "/predictor"], ["How we verify data", "/data"]];

export function Footer() {
  return (
    <footer className="mt-16 bg-navy text-white md:mt-28">
      <div className="mx-auto max-w-6xl px-4 pb-8 pt-10 md:pb-10 md:pt-16">
        <div className="grid grid-cols-2 gap-x-6 gap-y-8 md:grid-cols-[1.4fr_1fr_1fr] md:gap-12">
          <div className="col-span-2 md:col-span-1">
            <Logo onDark size={40} />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/65 md:text-[15px]">
              Real CAP cutoffs from the Maharashtra CET Cell, in one place. Independent — not affiliated with the CET Cell, DMER or MCC.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">Explore</p>
            <ul className="mt-3 space-y-2.5 text-sm md:text-[15px]">{NAV.map(([l, h]) => <li key={h}><Link href={h} className="text-white/85 hover:text-brand">{l}</Link></li>)}</ul>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">Official sources</p>
            <ul className="mt-3 space-y-2.5 text-sm md:text-[15px]">
              <li><a className="text-white/85 hover:text-brand" href="https://cetcell.mahacet.org/" target="_blank" rel="noreferrer">Maharashtra CET Cell ↗</a></li>
              <li><a className="text-white/85 hover:text-brand" href="https://fe2025.mahacet.org/" target="_blank" rel="noreferrer">FE CAP portal ↗</a></li>
            </ul>
          </div>
        </div>
        <p className="mt-10 border-t border-white/10 pt-6 text-xs md:mt-14 leading-relaxed text-white/50">
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
      <p role="note" className="flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-950 ring-1 ring-amber-200/70">
        <span className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" aria-hidden />
        <span><b>{preview.join(", ")}</b> is a preview awaiting CET Cell confirmation; everything else is checked against official PDFs. <a className="font-semibold underline" href="/data">How we verify</a></span>
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
      <div className="mx-auto max-w-6xl px-4 pb-5 pt-6 md:pb-8 md:pt-10">
        {crumb && <div className="mb-3 text-sm text-muted">{crumb}</div>}
        {eyebrow && <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-ink">{eyebrow}</p>}
        <h1 className="rise max-w-4xl text-[26px] font-bold leading-tight tracking-tight md:text-4xl">{title}</h1>
        {children && <div className="rise rise-2 mt-2 max-w-2xl text-[15px] leading-relaxed text-muted md:mt-3 md:text-base">{children}</div>}
      </div>
    </section>
  );
}
