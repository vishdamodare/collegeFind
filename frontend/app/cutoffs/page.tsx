import type { Metadata } from "next";
import CutoffExplorer from "@/components/CutoffExplorer";
import { PageHeader } from "@/components/Chrome";
import { get, Meta } from "@/lib/api";

export const metadata: Metadata = { title: "Cutoff Explorer" };

export default async function Cutoffs({ searchParams }: { searchParams: Promise<{ college?: string; branch?: string }> }) {
  const [sp, meta] = await Promise.all([searchParams, get<Meta>("/api/v1/meta")]);
  return (
    <main>
      <PageHeader title="Cutoff Explorer">Official closing cutoffs from the CET Cell CAP lists. Where a round has several stages, each stage is shown.</PageHeader>
      <div className="mx-auto max-w-6xl px-4 pb-8"><CutoffExplorer meta={meta} initial={sp} /></div>
    </main>
  );
}
