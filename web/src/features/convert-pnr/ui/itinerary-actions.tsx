import { Copy, Printer } from "lucide-react";

import { Button } from "@/shared/ui/button";

import type { ConvertRequest } from "../api/convert-pnr";
import { useCopyItineraryText, useOpenPrintableItinerary } from "../model/use-itinerary-export";

export function ItineraryActions({ request }: { request: ConvertRequest }) {
  const copyText = useCopyItineraryText();
  const openPrintable = useOpenPrintableItinerary();

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        disabled={copyText.isPending}
        onClick={() => {
          copyText.mutate(request);
        }}
      >
        <Copy aria-hidden />
        Copy text
      </Button>
      <Button
        variant="outline"
        size="sm"
        disabled={openPrintable.isPending}
        onClick={() => {
          openPrintable.mutate(request);
        }}
      >
        <Printer aria-hidden />
        Printable
      </Button>
    </>
  );
}
