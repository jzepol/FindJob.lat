export function OfferCardSkeleton() {
  return (
    <div className="card-premium rounded-2xl p-5 sm:p-6">
      <div className="flex gap-4">
        <div className="skeleton h-12 w-12 rounded-2xl" />
        <div className="flex-1 space-y-3">
          <div className="skeleton h-5 w-3/4 rounded-lg" />
          <div className="skeleton h-4 w-1/2 rounded-lg" />
          <div className="flex gap-2">
            <div className="skeleton h-6 w-16 rounded-full" />
            <div className="skeleton h-6 w-20 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  );
}