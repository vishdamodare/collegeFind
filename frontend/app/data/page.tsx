import type { Metadata } from "next";
import { PageHeader } from "@/components/Chrome";

export const metadata: Metadata = { title: "How we verify our data" };

const CHECKS: [string, string, string][] = [
  ["Independent re-extraction", "187,149 / 187,149", "A second extractor, written from scratch and never shown our first one, read all nine cutoff PDFs. Every stored rank, percentile, category, seat type and stage matched exactly."],
  ["Visual page audit", "1,119 values · 65 pages", "A reviewer looked at rendered PDF pages (including the hardest layouts) and checked every value sat under the right category column."],
  ["Completeness, both directions", "187,415 printed values", "Every value printed in the PDFs was counted against what we store. Nothing stored is missing from the PDF; the only values we lack are the documented gaps below."],
  ["Seat matrices", "5,743 / 5,743", "Intake figures for every course were re-extracted with a different method and matched exactly."],
  ["Source files", "12 / 12", "The official PDFs were downloaded again from the CET Cell and are byte-for-byte identical to the copies we imported."],
  ["What students receive", "≈89,700 checks", "The live API was tested against the database and against hand-computed results, including every safer / moderate / ambitious label."],
];

export default function DataPage() {
  return (
    <main>
      <PageHeader title="How we verify our data" eyebrow="Transparency">
        Everything on this site comes from official CET Cell PDFs. Here is exactly what was checked, what passed, and what we do not claim.
      </PageHeader>
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="text-2xl font-bold tracking-tight">What was checked</h2>
        <p className="mt-1 text-sm text-muted">Audit run on 10 Nov 2026 by seven independent checkers. All were read-only.</p>
        <ul className="mt-6 divide-y divide-line border-y border-line">
          {CHECKS.map(([t, n, d]) => (
            <li key={t} className="grid gap-1 py-5 md:grid-cols-[1fr_auto] md:gap-6">
              <div><h3 className="font-semibold">{t}</h3><p className="mt-1 text-[15px] leading-relaxed text-muted">{d}</p></div>
              <p className="num text-lg font-bold text-emerald-700 md:text-right">{n}</p>
            </li>
          ))}
        </ul>

        <h2 className="mt-14 text-2xl font-bold tracking-tight">Problems the audit found — and fixed</h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-[15px] leading-relaxed">
          <li>269 category codes had lost their last letter (<span className="num">PWDROBC</span> → <span className="num">PWDROBCS</span>).</li>
          <li>15 course names were cut short; 21 colleges showed an older name; 4 Government-Aided colleges were mislabelled; 255 colleges were missing their home university.</li>
          <li>26 cells the CET Cell prints with a percentile of 0 (Tuition Fee Waiver seats) are shown as “no percentile”, never as a real 0.</li>
        </ul>

        <h2 className="mt-14 text-2xl font-bold tracking-tight">What we do <u>not</u> claim</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-[15px] leading-relaxed">
          <li><b>This is automated cross-checking, not review by the CET Cell.</b> The values match the published PDFs; we cannot vouch for the PDFs themselves.</li>
          <li><b>Every printed cut-off value is stored.</b> Very wide tables print their last columns on the next page without a course name; we match those 266 values to their course by their exact position on the page, and only when the match is unique.</li>
          <li><b>2022-23 Round 1 is marked “preview”.</b> The file is titled “All India Seats” by the CET Cell, but its content is the Maharashtra list. We are waiting for confirmation.</li>
          <li><b>2024 ranks are not one scale.</b> The official 2024 lists print ranks that are not comparable across categories. That is how they are published, so the predictor compares percentiles only.</li>
          <li><b>COEP appears twice</b> (codes 06006 and 16006) because the CET Cell re-coded the institution in 2024.</li>
          <li><b>Not included yet:</b> fees, addresses, placements and NIRF rank (no official source loaded), All-India lists, JEE Main and NEET UG.</li>
        </ul>
        <p className="mt-10 rounded-lg bg-navy/[.05] px-4 py-3 text-sm text-muted">Historical cutoffs never guarantee future admission. Always confirm on the official CAP portal.</p>
      </div>
    </main>
  );
}
