import type { Metadata } from "next";
import Predictor from "@/components/Predictor";
import { PageHeader } from "@/components/Chrome";
import { get, Meta } from "@/lib/api";

export const metadata: Metadata = { title: "College Predictor" };

export default async function Page({ searchParams }: { searchParams: Promise<{ percentile?: string }> }) {
  const [sp, meta] = await Promise.all([searchParams, get<Meta>("/api/v1/meta")]);
  return (
    <main>
      <PageHeader title="College Predictor">Compare your percentile with past closing cutoffs. This is a historical comparison, not a guarantee of admission.</PageHeader>
      <div className="mx-auto max-w-6xl px-4 pb-8"><Predictor meta={meta} initialPct={sp.percentile ?? ""} /></div>
    </main>
  );
}
