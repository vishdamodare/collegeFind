"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Logo } from "./Logo";

const NAV = [["Home", "/"], ["Colleges", "/colleges"], ["Cutoffs", "/cutoffs"], ["Predictor", "/predictor"]];

export default function Nav() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const active = (h: string) => path === h || path.startsWith(h + "/");
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-background/90 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 md:h-[68px]">
        <Link href="/" aria-label="Maharashtra College Finder — home" onClick={() => setOpen(false)}>
          <span className="md:hidden"><Logo size={34} /></span><span className="hidden md:inline"><Logo size={44} /></span>
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {NAV.map(([l, h]) => (
            <Link key={h} href={h} aria-current={active(h) ? "page" : undefined}
              className={`relative px-4 py-2 text-[15px] font-medium transition-colors hover:text-brand-ink ${active(h) ? "text-navy" : "text-muted"}`}>
              {l}
              {active(h) && <span className="absolute inset-x-4 -bottom-[14px] h-[3px] rounded-t bg-brand" />}
            </Link>
          ))}
          <Link href="/predictor" className="ml-4 rounded-lg bg-navy px-5 py-2.5 text-[15px] font-semibold text-white transition hover:bg-brand hover:text-navy">
            Find my college →
          </Link>
        </nav>

        <button className="-mr-2 grid h-11 w-11 place-items-center rounded-lg md:hidden" aria-expanded={open} aria-controls="mobile-nav" aria-label="Menu" onClick={() => setOpen(!open)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>{open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}</svg>
        </button>
      </div>
      {open && (
        <nav id="mobile-nav" aria-label="Mobile" className="absolute inset-x-0 top-full h-[calc(100dvh-3.5rem)] border-t border-line bg-background px-4 pb-6 pt-2 md:hidden">
          {[...NAV, ["How we verify data", "/data"]].map(([l, h]) => (
            <Link key={h} href={h} onClick={() => setOpen(false)} aria-current={active(h) ? "page" : undefined}
              className={`flex items-center justify-between border-b border-line py-4 text-lg font-semibold ${active(h) ? "text-brand-ink" : ""}`}>{l}<span aria-hidden className="text-muted">→</span></Link>
          ))}
          <Link href="/predictor" onClick={() => setOpen(false)} className="mt-6 block rounded-xl bg-brand px-3 py-4 text-center font-bold text-navy">Find my college →</Link>
        </nav>
      )}
    </header>
  );
}
