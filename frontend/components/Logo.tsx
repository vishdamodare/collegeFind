import { useId } from "react";

/**
 * Original mark: a large mortarboard behind a location pin — "find your college".
 * The cap uses currentColor so it stays legible on both light and dark backgrounds
 * (pass text-navy on light, text-white on dark). The gap around the pin is a real cut-out (transparent).
 */
export function LogoMark({ size = 44, className = "text-navy" }: { size?: number; className?: string }) {
  const id = useId();
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} className={className} aria-hidden="true">
      <defs>
        <mask id={id}>
          <rect width="64" height="64" fill="#fff" />
          <path d="M43 63C43 63 28 50.6 28 40a15 15 0 0 1 30 0C58 50.6 43 63 43 63Z" fill="#000" stroke="#000" strokeWidth="7" strokeLinejoin="round" />
        </mask>
      </defs>
      <g mask={`url(#${id})`} fill="currentColor">
        <path d="M4 25 34 8 60 19 30 34Z" />
        <path d="M15 30.5V41c0 4.4 9 7.6 16 7.6V34Z" />
        <path d="M7 28v17" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" fill="none" />
        <circle cx="7" cy="47" r="3" />
        <path d="M4.4 49.5h5.2l1 9H3.4Z" />
      </g>
      <path d="M43 63C43 63 28 50.6 28 40a15 15 0 0 1 30 0C58 50.6 43 63 43 63ZM37.4 40a5.6 5.6 0 1 0 11.2 0a5.6 5.6 0 1 0 -11.2 0Z" fill="#ff6600" fillRule="evenodd" />
    </svg>
  );
}

/** Mark + two-line wordmark. `onDark` flips cap and text colours for dark backgrounds. */
export function Logo({ onDark = false, size = 46 }: { onDark?: boolean; size?: number }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark size={size} className={onDark ? "text-white" : "text-navy"} />
      <span className="leading-none">
        <span className={`block text-[10px] font-semibold uppercase tracking-[0.22em] ${onDark ? "text-white/60" : "text-muted"}`}>Maharashtra</span>
        <span className={`mt-1 block text-[19px] font-bold tracking-tight ${onDark ? "text-white" : "text-navy"}`}>College Finder</span>
      </span>
    </span>
  );
}
