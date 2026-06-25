import { Suspense } from "react";
import { JobsPageClient } from "@/components/jobs-page-client";
import { OfferCardSkeleton } from "@/components/offer-card-skeleton";
import { getSources } from "@/lib/api";

export default async function JobsPage() {
  let sources: { slug: string; name: string }[] = [];
  try {
    const data = await getSources();
    sources = data.map((s) => ({ slug: s.slug, name: s.name }));
  } catch {
    sources = [
      { slug: "computrabajo", name: "Computrabajo" },
      { slug: "bumeran", name: "Bumeran" },
      { slug: "remoteok", name: "Remote OK" },
    ];
  }

  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-7xl space-y-4 px-4 py-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <OfferCardSkeleton key={i} />
          ))}
        </div>
      }
    >
      <JobsPageClient sources={sources} />
    </Suspense>
  );
}