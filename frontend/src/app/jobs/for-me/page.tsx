import { Suspense } from "react";
import { ForMePageClient } from "@/components/for-me-page-client";
import { OfferCardSkeleton } from "@/components/offer-card-skeleton";

export const metadata = {
  title: "Para vos | Findjob.lat",
  description: "Ofertas recomendadas según tu CV y preferencias",
};

export default function ForMePage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-4xl space-y-4 px-4 py-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <OfferCardSkeleton key={i} />
          ))}
        </div>
      }
    >
      <ForMePageClient />
    </Suspense>
  );
}