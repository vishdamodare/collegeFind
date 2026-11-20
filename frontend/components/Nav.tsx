"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Logo } from "./Logo";

const NAV = [["Colleges", "/colleges"], ["Cutoffs", "/cutoffs"], ["Predictor", "/predictor"]];

export default function Nav() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const active = (h: string) => path === h || path.startsWith(h + "/");
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-background/90 backdrop-blur-md">
      <div className="mx-auto flex h-[68px] max-w-6xl items-center justify-between px-4">
        <Link href="/" aria-label="Maharashtra College Finder — home"><Logo size={46} /></Link>

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {NAV.map(([l, h]) => (
            <Link key={h} href={h} aria-current={active(h) ? "page" : undefined}
              className={`relative px-4 py-2 text-[15px] font-medium transition-colors hover:text-brand-ink ${active(h) ? "text-navy" : "text-muted"}`}>
              {l}
              {active(h) && <span className="absolute inset-x-4 -bottom-[13px] h-[3px] rounded-t bg-brand" />}
            </Link>
          ))}
          <Link href="/predictor" className="ml-4 rounded-lg bg-navy px-5 py-2.5 text-[15px] font-semibold text-white transition hover:bg-brand hover:text-navy">
            Find my college →
          </Link>
        </nav>

        <button className="grid h-10 w-10 place-items-center rounded-lg border border-line md:hidden" aria-expanded={open} aria-controls="mobile-nav" aria-label="Menu" onClick={() => setOpen(!open)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>{open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}</svg>
        </button>
      </div>
      {open && (
        <nav id="mobile-nav" aria-label="Mobile" className="border-t border-line bg-background px-4 pb-4 md:hidden">
          {NAV.map(([l, h]) => (
            <Link key={h} href={h} onClick={() => setOpen(false)} className={`block border-b border-line px-1 py-3.5 text-lg font-medium ${active(h) ? "text-brand-ink" : ""}`}>{l}</Link>
          ))}
          <Link href="/predictor" onClick={() => setOpen(false)} className="mt-4 block rounded-lg bg-brand px-3 py-3.5 text-center font-semibold text-navy">Find my college →</Link>
        </nav>
      )}
    </header>
  );
}
