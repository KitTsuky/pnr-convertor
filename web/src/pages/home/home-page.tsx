import { FileText, Plane, ServerCrash } from "lucide-react";
import { useRef, useState } from "react";

import { ItineraryDetails } from "@/entities/itinerary";
import {
  ConvertPnrForm,
  ItineraryActions,
  toConvertRequest,
  useConvertPnr,
  type ConvertRequest,
} from "@/features/convert-pnr";
import type { ApiError } from "@/shared/api/api-error";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
import { Card, CardContent } from "@/shared/ui/card";
import { Skeleton } from "@/shared/ui/skeleton";

export function HomePage() {
  const conversion = useConvertPnr();
  const [request, setRequest] = useState<ConvertRequest | null>(null);
  const resultRef = useRef<HTMLElement>(null);

  return (
    <div className="min-h-dvh">
      <header className="border-b bg-card/60 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-2 px-4">
          <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Plane className="size-4" aria-hidden />
          </span>
          <span className="font-semibold tracking-tight">PNR Convertor</span>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
        <div className="lg:sticky lg:top-8 lg:self-start">
          <h1 className="text-2xl font-semibold tracking-tight">Turn a PNR into an itinerary</h1>
          <p className="mt-1 mb-6 text-sm text-muted-foreground">
            Paste a booking from any major GDS and get local times, durations and connections.
          </p>
          <Card>
            <CardContent>
              <ConvertPnrForm
                isPending={conversion.isPending}
                onSubmit={(values) => {
                  const next = toConvertRequest(values);
                  setRequest(next);
                  conversion.mutate(next, {
                    // On narrow screens the result sits below the form: bring it into view.
                    onSettled: () => resultRef.current?.scrollIntoView({ behavior: "smooth" }),
                  });
                }}
                onReset={() => {
                  setRequest(null);
                  conversion.reset();
                }}
              />
            </CardContent>
          </Card>
        </div>

        <section
          ref={resultRef}
          className="scroll-mt-4"
          aria-live="polite"
          aria-busy={conversion.isPending}
          aria-label="Itinerary"
        >
          {conversion.isPending ? (
            <ResultSkeleton />
          ) : conversion.isError ? (
            <ErrorState error={conversion.error} />
          ) : conversion.isSuccess && request ? (
            <ItineraryDetails
              itinerary={conversion.data}
              actions={<ItineraryActions request={request} />}
            />
          ) : (
            <EmptyState />
          )}
        </section>
      </main>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-80 flex-col items-center justify-center rounded-xl border border-dashed p-10 text-center">
      <FileText className="size-8 text-muted-foreground" aria-hidden />
      <p className="mt-3 font-medium">Your itinerary will appear here</p>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        Paste a PNR on the left, or try the example, then convert.
      </p>
    </div>
  );
}

function ErrorState({ error }: { error: ApiError }) {
  return (
    <Alert>
      <ServerCrash aria-hidden />
      <AlertTitle>{error.problem?.title ?? "Conversion failed"}</AlertTitle>
      <AlertDescription>{error.message}</AlertDescription>
    </Alert>
  );
}

function ResultSkeleton() {
  return (
    <div className="flex flex-col gap-4" aria-label="Loading itinerary">
      <Skeleton className="h-24 rounded-xl" />
      <Skeleton className="h-32 rounded-xl" />
      <Skeleton className="h-72 rounded-xl" />
    </div>
  );
}
